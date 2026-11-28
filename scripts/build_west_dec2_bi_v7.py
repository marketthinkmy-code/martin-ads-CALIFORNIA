"""US West 12/2 live — Business & Industry × 新馬 V7 (operator 2026-11-28: 「全部跟你的建议」).

Business & Industry was the only interest audience that registered this week (V1: RM170 / 3 reg,
CPL ≈ 57); 新馬 V7 is the video Meta favoured in the CBO tests and the one bringing parents of
10+ children. One new ad set in the interest × V1 campaign, same audience as the B&I ad set,
video 新馬 V7, RM50/day, age 35–65, Advantage+ audience OFF, FB/IG/WhatsApp/Threads (no Audience
Network), end 12/3 09:00 +0800. Built PAUSED. Idempotent by name.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_west_ab_nov as west  # noqa: E402
from build_west_ab_nov import throttle_tolerant  # noqa: E402

from adbot.commands import graph_client  # noqa: E402
from adbot.settings import load_settings  # noqa: E402

ACCT = west.ACCT
CAMPAIGN_ID = "120249371380290259"          # US West | 州级 | 兴趣 × V1 | 12/2 live
SOURCE = "120235284014140259"               # historic Business & Industry ad set (interests)
NAME = "Business & Industry | 州级 CA+WA | 新馬 V7"
AD_NAME = "新馬 Video 7：14歲了，還有機會長高嗎"
V7_CREATIVE = "1178236997968310"
DAILY = 5000
END_TIME = "2026-12-03T09:00:00+0800"


def strip(flex):
    out = []
    for block in flex:
        nb = {k: [{"id": str(i["id"])} for i in v if isinstance(i, dict) and i.get("id")]
              for k, v in block.items() if isinstance(v, list)}
        nb = {k: v for k, v in nb.items() if v}
        if nb:
            out.append(nb)
    return out


def main() -> None:
    g = throttle_tolerant(graph_client(load_settings()))
    flex = strip(g._request("GET", SOURCE, params={"fields": "targeting"})["targeting"].get("flexible_spec", []))
    tgt = {"geo_locations": {"regions": west.RESOLVED_STATES, "location_types": ["home", "recent"]},
           "locales": [20, 21, 22], "excluded_custom_audiences": west.EXCLUDE,
           "age_min": 35, "age_max": 65, "targeting_automation": {"advantage_audience": 0},
           "flexible_spec": flex,
           "publisher_platforms": ["facebook", "instagram", "whatsapp", "threads"]}
    have = {r["name"]: r["id"] for r in g._get_all(f"{CAMPAIGN_ID}/adsets", {"fields": "id,name"})}
    asid = have.get(NAME)
    if not asid:
        asid = g.create_adset(
            ACCT, campaign_id=CAMPAIGN_ID, name=NAME, daily_budget=DAILY, end_time=END_TIME,
            bid_strategy="LOWEST_COST_WITHOUT_CAP", optimization_goal="OFFSITE_CONVERSIONS",
            billing_event="IMPRESSIONS",
            promoted_object={"pixel_id": west.PIXEL_ID, "custom_event_type": "COMPLETE_REGISTRATION"},
            targeting=tgt, status="PAUSED")["id"]
        time.sleep(3)
    print(f"ad set {asid} {NAME}", flush=True)
    ads = {r["name"]: r["id"] for r in g._get_all(f"{asid}/ads", {"fields": "id,name"})}
    adid = ads.get(AD_NAME) or g.create_ad(ACCT, name=AD_NAME, adset_id=asid,
                                           creative={"creative_id": V7_CREATIVE}, status="PAUSED")["id"]
    print(f"ad {adid} {AD_NAME}", flush=True)
    a = g._request("GET", asid, params={"fields": "id,name,status,daily_budget,end_time,targeting"})
    t = a["targeting"]
    print(json.dumps({"id": a["id"], "status": a["status"], "daily_budget": a["daily_budget"],
                      "end_time": a.get("end_time"), "age": [t.get("age_min"), t.get("age_max")],
                      "adv": t.get("targeting_automation"), "platforms": t.get("publisher_platforms"),
                      "flex_items": sum(len(v) for b in t.get("flexible_spec") or [] for v in b.values())},
                     ensure_ascii=False))
    print("DONE")


if __name__ == "__main__":
    main()
