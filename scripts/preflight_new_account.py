"""Read-only PREFLIGHT for the new ad account: can we actually run ads in it?

Operator asked for certainty, not guesses, so this checks every prerequisite for a
build and prints PASS/FAIL per item instead of inferring from one call:

  1. token identity + whether it can read the account at all
  2. account health   : status, currency, timezone, spend cap, funding source
  3. Page             : is a promotable Page attached (creatives need one)
  4. Pixel            : is 2035639583602118 visible in the account
  5. Exclusion audience: any custom audiences yet
  6. WRITE capability : create a PAUSED campaign, read it back, then DELETE it.
     Read access does not imply write access, and the only honest way to know
     whether a build will succeed is to perform one and roll it back.
"""
from __future__ import annotations

import os

from adbot.commands import graph_client
from adbot.logging import final_summary, get_logger
from adbot.newbm import new_bm_client
from adbot.settings import load_settings

ACCT = "act_2022836788419850"
WANT_PIXEL = "2035639583602118"
WANT_PAGE = "1180683238455992"

results: list[tuple[str, bool, str]] = []


def check(log, label, fn):
    try:
        ok, detail = fn()
    except Exception as e:  # noqa: BLE001 - preflight reports failures, never raises
        ok, detail = False, str(e)
    results.append((label, ok, detail))
    log.info("%s %s — %s", "✅ PASS" if ok else "❌ FAIL", label, detail)


def main() -> None:
    log = get_logger()
    # Prefer the new business's own token when it exists; fall back to the repo token so
    # this preflight still reports the real blocker instead of refusing to run.
    if os.environ.get("META_NEW_BM_TOKEN", "").strip():
        g = new_bm_client()
        log.info("using META_NEW_BM_TOKEN")
    else:
        g = graph_client(load_settings())
        log.info("using META_SYSTEM_USER_TOKEN (META_NEW_BM_TOKEN not set)")

    me = g._request("GET", "me", params={"fields": "id,name"})
    log.info("token = system user %s (%s)", me.get("id"), me.get("name"))
    log.info("=" * 70)

    def read_account():
        r = g.get_object(ACCT, "id,name,account_status,currency,timezone_name,"
                               "spend_cap,amount_spent,funding_source,disable_reason")
        detail = (f"{r.get('name')} · status={r.get('account_status')} · {r.get('currency')} · "
                  f"{r.get('timezone_name')} · funding={r.get('funding_source')} · "
                  f"disable_reason={r.get('disable_reason')}")
        return r.get("account_status") == 1, detail

    check(log, "1. account readable + ACTIVE", read_account)

    def pages():
        r = g._request("GET", f"{ACCT}/promote_pages", params={"fields": "id,name", "limit": 25})
        rows = r.get("data", [])
        if not rows:
            return False, "no promotable Page attached — creatives cannot be built"
        names = ", ".join(f"{p.get('name')}({p.get('id')})" for p in rows)
        return any(str(p.get("id")) == WANT_PAGE for p in rows), f"{len(rows)} page(s): {names}"

    check(log, f"2. Page {WANT_PAGE} attached", pages)

    def pixels():
        r = g._request("GET", f"{ACCT}/adspixels", params={"fields": "id,name", "limit": 25})
        rows = r.get("data", [])
        if not rows:
            return False, "no pixel on the account"
        names = ", ".join(f"{p.get('name')}({p.get('id')})" for p in rows)
        return any(str(p.get("id")) == WANT_PIXEL for p in rows), f"{len(rows)} pixel(s): {names}"

    check(log, f"3. Pixel {WANT_PIXEL} usable", pixels)

    def audiences():
        r = g._request("GET", f"{ACCT}/customaudiences",
                       params={"fields": "id,name,subtype", "limit": 25})
        rows = r.get("data", [])
        if not rows:
            return False, "none yet — exclusion audience must be rebuilt in this account"
        return True, ", ".join(f"{a.get('name')}({a.get('id')})" for a in rows)

    check(log, "4. custom audiences present", audiences)

    # 5. the real test: can this token WRITE? build a paused campaign and delete it.
    created = {"id": None}

    def write_test():
        c = g.create_campaign(ACCT, name="[PREFLIGHT] delete me", objective="OUTCOME_SALES",
                              buying_type="AUCTION", status="PAUSED", special_ad_categories=[],
                              is_adset_budget_sharing_enabled=False)
        created["id"] = c["id"]
        back = g.get_object(c["id"], "id,name,status")
        return back.get("status") == "PAUSED", f"created + read back campaign {c['id']}"

    check(log, "5. WRITE: create campaign", write_test)

    if created["id"]:
        def cleanup():
            g._request("DELETE", created["id"])
            return True, f"deleted {created['id']}"
        check(log, "6. cleanup: delete test campaign", cleanup)

    log.info("=" * 70)
    failed = [l for l, ok, _ in results if not ok]
    if failed:
        log.info("BLOCKERS (%d):", len(failed))
        for l in failed:
            log.info("   ✗ %s", l)
    final_summary(log, "ALL CHECKS PASSED — account is ready to build in"
                  if not failed else f"NOT READY — {len(failed)} blocker(s): {'; '.join(failed)}")


if __name__ == "__main__":
    main()
