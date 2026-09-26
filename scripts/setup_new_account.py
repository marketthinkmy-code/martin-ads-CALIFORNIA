"""One-shot SETUP for the new ad account so it can actually run ads.

Fixes the three preflight blockers with two tokens:
  OLD token (ads-my in MTC X Martin, owns the pixel + the reference audience)
    1. share pixel 2035639583602118 to the new ad account (cross-business share)
    2. read the rule of the existing exclusion audience so it can be cloned exactly
  NEW token (ads-my in the new business, has the new ad account)
    3. rebuild the exclusion audience in the new account from that rule
    4. prove a creative can be built with the Page (promote_pages was empty, but the
       system user has Ads access on the Page, so the only honest test is to try) —
       builds a link creative and deletes it.
Idempotent: every step checks before writing.
"""
from __future__ import annotations

import json

from adbot.commands import graph_client
from adbot.logging import final_summary, get_logger
from adbot.newbm import NEW_ACCT, new_bm_client
from adbot.settings import load_settings

NEW_ACCT_NUM = NEW_ACCT.replace("act_", "")
NEW_BUSINESS = "1039134515617251"
PIXEL_ID = "2035639583602118"
PAGE_ID = "1180683238455992"
REF_AUDIENCE = "120254451454600558"  # [美東美中 US] 15days complete registration (reference)
REF_AUDIENCE_FALLBACK = "120254451454000558"
LINK = "https://kidsgrowthformula.com/us-register"


def main() -> None:
    log = get_logger()
    old = graph_client(load_settings())
    new = new_bm_client()
    ok, fails = [], []

    # ── 1. share pixel to the new account ────────────────────────────────────
    try:
        shared = old._request("GET", f"{PIXEL_ID}/shared_accounts",
                              params={"business": NEW_BUSINESS, "limit": 50}).get("data", [])
        if any(str(a.get("id", "")).replace("act_", "") == NEW_ACCT_NUM for a in shared):
            log.info("1. pixel already shared to %s", NEW_ACCT)
        else:
            old._request("POST", f"{PIXEL_ID}/shared_accounts",
                         data={"account_id": NEW_ACCT_NUM, "business": NEW_BUSINESS})
            log.info("1. ✅ shared pixel %s -> %s", PIXEL_ID, NEW_ACCT)
        ok.append("pixel shared")
    except Exception as e:  # noqa: BLE001
        log.info("1. ❌ pixel share failed: %s", e)
        fails.append(f"pixel share: {e}")

    # verify from the NEW side
    try:
        px = new._request("GET", f"{NEW_ACCT}/adspixels", params={"fields": "id,name"}).get("data", [])
        log.info("   new account now sees pixels: %s", [(p["id"], p.get("name")) for p in px])
        if not any(str(p["id"]) == PIXEL_ID for p in px):
            fails.append("pixel not visible from new account after share")
    except Exception as e:  # noqa: BLE001
        log.info("   pixel verify failed: %s", e)
        fails.append(f"pixel verify: {e}")

    # ── 2. read the reference exclusion audience rule ────────────────────────
    rule, retention, ref_name = None, 15, None
    for aid in (REF_AUDIENCE, REF_AUDIENCE_FALLBACK):
        try:
            r = old.get_object(aid, "id,name,rule,retention_days,subtype,pixel_id")
            rule, retention, ref_name = r.get("rule"), r.get("retention_days") or 15, r.get("name")
            log.info("2. reference audience %s '%s' retention=%s rule=%s",
                     aid, ref_name, retention, rule)
            break
        except Exception as e:  # noqa: BLE001
            log.info("2. could not read %s: %s", aid, e)
    if not rule:
        # Fallback: the standard "CompleteRegistration in last N days" website rule
        rule = json.dumps({"inclusions": {"operator": "or", "rules": [{
            "event_sources": [{"id": PIXEL_ID, "type": "pixel"}],
            "retention_seconds": 15 * 86400,
            "filter": {"operator": "and", "filters": [
                {"field": "event", "operator": "eq", "value": "CompleteRegistration"}]}}]}})
        log.info("2. using fallback rule (CompleteRegistration, 15d)")
    elif not isinstance(rule, str):
        rule = json.dumps(rule)

    # ── 3. rebuild it in the new account ─────────────────────────────────────
    new_aud_name = "[NEW 美东美中 US] 15days complete registration"
    try:
        existing = new._request("GET", f"{NEW_ACCT}/customaudiences",
                                params={"fields": "id,name", "limit": 100}).get("data", [])
        hit = next((a for a in existing if a.get("name") == new_aud_name), None)
        if hit:
            log.info("3. audience already exists: %s", hit["id"])
        else:
            # the rule must reference the pixel by id; it is the same pixel so no rewrite needed
            created = new._request("POST", f"{NEW_ACCT}/customaudiences", data={
                "name": new_aud_name, "subtype": "WEBSITE", "rule": rule,
                "retention_days": retention, "prefill": "true",
                "description": f"cloned from {ref_name or 'reference'} for the new account"})
            log.info("3. ✅ created exclusion audience %s", created.get("id"))
        ok.append("exclusion audience")
    except Exception as e:  # noqa: BLE001
        log.info("3. ❌ audience create failed: %s", e)
        fails.append(f"audience: {e}")

    # ── 4. can we build a creative with the Page? ────────────────────────────
    cid = None
    try:
        c = new._request("POST", f"{NEW_ACCT}/adcreatives", data={
            "name": "[PREFLIGHT] page test - delete me",
            "object_story_spec": json.dumps({"page_id": PAGE_ID, "link_data": {
                "link": LINK, "message": "preflight",
                "picture": "https://www.facebook.com/images/fb_icon_325x325.png"}})})
        cid = c.get("id")
        log.info("4. ✅ creative with Page %s built: %s", PAGE_ID, cid)
        ok.append("page usable in creatives")
    except Exception as e:  # noqa: BLE001
        log.info("4. ❌ creative with Page failed: %s", e)
        fails.append(f"page creative: {e}")
    finally:
        if cid:
            try:
                new._request("DELETE", cid)
                log.info("   cleaned up test creative %s", cid)
            except Exception as e:  # noqa: BLE001
                log.info("   cleanup failed for %s: %s", cid, e)

    log.info("=" * 70)
    final_summary(log, f"OK: {ok} · FAIL: {fails}" if fails else f"ALL SET: {ok}")


if __name__ == "__main__":
    main()
