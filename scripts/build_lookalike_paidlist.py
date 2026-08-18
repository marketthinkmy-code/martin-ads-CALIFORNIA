"""Build a fresh customer-list custom audience from the current Paid Student List, then
create the 1% / 1-2% / 2-3% / 3-4% / 4-5% US lookalikes off it.

Operator asked to rebuild the paid-list lookalike from the up-to-date sheet (the existing
`US PAID STUDENTS MAY 2026` source is from May). PII (email/phone) is read, normalised and
SHA-256 hashed INSIDE the runner — only hashes are ever sent to Meta, and nothing is printed.

Sheet: config cpa.spreadsheet_id · tab identified by gid (sheetId) 1292000535.
"""
from __future__ import annotations

import hashlib
import json
import re
import datetime as dt

from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.logging import final_summary, get_logger
from adbot.settings import load_settings

GID = 1292000535                     # the tab the operator linked
COUNTRY = "US"
RATIOS = [(0.0, 0.01), (0.01, 0.02), (0.02, 0.03), (0.03, 0.04), (0.04, 0.05)]


def _sha(v: str) -> str:
    return hashlib.sha256(v.encode("utf-8")).hexdigest()


def norm_email(v: str) -> str:
    v = (v or "").strip().lower()
    return v if "@" in v and "." in v.split("@")[-1] else ""


def norm_phone(v: str) -> str:
    d = re.sub(r"\D", "", v or "")
    if len(d) < 7:
        return ""
    if len(d) == 10:      # bare US number -> add country code
        d = "1" + d
    return d


def main() -> None:
    log = get_logger()
    s = load_settings()
    g = graph_client(s)
    acct = s.meta.account_path
    ssid = s.cpa.spreadsheet_id

    sc = SheetsClient(s.secrets.google_sa_json)
    meta = (sc._svc.spreadsheets()
            .get(spreadsheetId=ssid, fields="sheets.properties(title,sheetId)").execute())
    tab = next((sh["properties"]["title"] for sh in meta.get("sheets", [])
                if sh["properties"].get("sheetId") == GID), None)
    if not tab:
        raise SystemExit(f"no tab with gid {GID} in workbook")
    log.info("reading tab %r (gid %s)", tab, GID)
    rows = sc.read_tab(ssid, tab)
    if not rows:
        raise SystemExit("tab is empty")

    # locate header row + email / phone columns
    hdr_idx = email_col = phone_col = None
    for i, row in enumerate(rows[:20]):
        low = [str(c).strip().lower() for c in row]
        ecol = next((j for j, c in enumerate(low) if c == "email" or "email" in c), None)
        if ecol is not None:
            hdr_idx, email_col = i, ecol
            phone_col = next((j for j, c in enumerate(low)
                              if "whatsapp" in c or "phone" in c or "號碼" in c or "号码" in c), None)
            break
    if email_col is None:
        raise SystemExit("could not find an email column")
    log.info("header row=%d · email col=%s · phone col=%s", hdr_idx, email_col, phone_col)

    data, n_email, n_phone = [], 0, 0
    for row in rows[hdr_idx + 1:]:
        e = norm_email(row[email_col]) if len(row) > email_col else ""
        p = norm_phone(row[phone_col]) if (phone_col is not None and len(row) > phone_col) else ""
        if not e and not p:
            continue
        if e:
            n_email += 1
        if p:
            n_phone += 1
        data.append([_sha(e) if e else "", _sha(p) if p else ""])

    if len(data) < 100:
        log.warning("only %d rows with email/phone — Meta needs ~100 matched for a lookalike; "
                    "proceeding, Meta will reject if the matched seed is too small", len(data))
    log.info("prepared %d rows (%d emails, %d phones) — hashed, no PII leaves the runner",
             len(data), n_email, n_phone)

    # 1) create the customer-list custom audience
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date().isoformat()
    src_name = f"US PAID STUDENTS {today}"
    src = g._request("POST", f"{acct}/customaudiences", data={
        "name": src_name, "subtype": "CUSTOM",
        "customer_file_source": "USER_PROVIDED_ONLY",
        "description": "Paid Student List (auto-refreshed from sheet)",
    })
    src_id = src["id"]
    log.info("created source custom audience %s (%s)", src_id, src_name)

    # 2) upload the hashed users
    up = g._request("POST", f"{src_id}/users", data={"payload": json.dumps(
        {"schema": ["EMAIL", "PHONE"], "data": data})})
    log.info("uploaded users -> %s", json.dumps(up))

    # 3) build the 1% / 1-2% / 2-3% / 3-4% / 4-5% US lookalikes
    made = []
    for start, ratio in RATIOS:
        band = f"{int(ratio*100)}%" if start == 0 else f"{int(start*100)}%-{int(ratio*100)}%"
        spec = {"country": COUNTRY, "ratio": ratio}
        if start > 0:
            spec["starting_ratio"] = start
        lal = g._request("POST", f"{acct}/customaudiences", data={
            "name": f"Lookalike (US, {band}) - {src_name}",
            "subtype": "LOOKALIKE", "origin_audience_id": src_id,
            "lookalike_spec": json.dumps(spec)})
        made.append((band, lal["id"]))
        log.info("  lookalike %-6s -> %s", band, lal["id"])

    log.info("=" * 60)
    log.info("source: %s -> %s", src_name, src_id)
    for band, aid in made:
        log.info("  %-6s %s", band, aid)
    final_summary(log, f"Paid-list lookalikes built: source {src_id} ({len(data)} seed rows) + "
                       f"{len(made)} US lookalikes (1%%..5%%).")


if __name__ == "__main__":
    main()
