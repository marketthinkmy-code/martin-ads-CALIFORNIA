"""READ-ONLY audit: show exactly what was read from the Paid Student List tab and uploaded
to the paid-list custom audience. No writes to Meta. Emails/phones are masked so the full
PII does not land in the chat transcript — the operator cross-checks against their own sheet.
"""
from __future__ import annotations

import re

from adbot.clients.sheets import SheetsClient
from adbot.logging import get_logger
from adbot.settings import load_settings

GID = 1292000535


def mask_email(v: str) -> str:
    v = (v or "").strip()
    if "@" not in v:
        return "(no email)"
    local, _, dom = v.partition("@")
    keep = local[:2]
    return f"{keep}{'*' * max(1, len(local) - 2)}@{dom}"


def mask_phone(v: str) -> str:
    d = re.sub(r"\D", "", v or "")
    if len(d) < 4:
        return "(no phone)"
    return f"{'*' * (len(d) - 4)}{d[-4:]}"


def main() -> None:
    log = get_logger()
    s = load_settings()
    ssid = s.cpa.spreadsheet_id
    sc = SheetsClient(s.secrets.google_sa_json)

    meta = (sc._svc.spreadsheets()
            .get(spreadsheetId=ssid, fields="sheets.properties(title,sheetId)").execute())
    tab = next((sh["properties"]["title"] for sh in meta.get("sheets", [])
                if sh["properties"].get("sheetId") == GID), None)
    log.info("workbook %s · tab for gid %s = %r", ssid, GID, tab)
    rows = sc.read_tab(ssid, tab)

    hdr_idx = email_col = phone_col = name_col = None
    for i, row in enumerate(rows[:20]):
        low = [str(c).strip().lower() for c in row]
        ecol = next((j for j, c in enumerate(low) if c == "email" or "email" in c), None)
        if ecol is not None:
            hdr_idx, email_col = i, ecol
            phone_col = next((j for j, c in enumerate(low)
                              if "whatsapp" in c or "phone" in c or "號碼" in c or "号码" in c), None)
            name_col = next((j for j, c in enumerate(low)
                             if "名" in c or c == "name" or "姓" in c), None)
            break
    log.info("header row=%s (%s)", hdr_idx, rows[hdr_idx] if hdr_idx is not None else None)
    log.info("columns -> name=%s email=%s phone=%s", name_col, email_col, phone_col)

    used = skipped = 0
    log.info("=" * 70)
    log.info("%-4s %-16s %-28s %s", "#", "name", "email (masked)", "phone (masked)")
    log.info("-" * 70)
    for row in rows[hdr_idx + 1:]:
        e = row[email_col] if len(row) > email_col else ""
        p = row[phone_col] if (phone_col is not None and len(row) > phone_col) else ""
        nm = row[name_col] if (name_col is not None and len(row) > name_col) else ""
        if not (e or "").strip() and not (p or "").strip():
            skipped += 1
            continue
        used += 1
        log.info("%-4d %-16s %-28s %s", used, (nm or "")[:16], mask_email(e), mask_phone(p))
    log.info("=" * 70)
    log.info("TOTAL uploaded rows=%d · skipped (no email+phone)=%d", used, skipped)


if __name__ == "__main__":
    main()
