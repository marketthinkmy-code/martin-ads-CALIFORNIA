"""US West 12/2 live — three CBO 1-1-3 audience campaigns (operator 2026-11-27).

Operator: 「A but CBO 1-1-3 / 每个 campaign 1 个 ad set，放 3 支赢的视频（V5 / V6 / V7）/
Campaign 选择：Parents 3-17 + Engaged, Family & Relationships, Food & Drink + Milk /
CBO RM100 per day」.
  * one campaign per audience, budget on the campaign (CBO) RM100/day, 1 ad set, 3 ads —
    the three Broad A+ winners this week (新V5 / 新V6 / 新馬 V7, CPL ≈ 46–53), existing creatives
  * whole CA + WA, Chinese locales, registrants / paid lists excluded, age 35–65,
    Advantage+ audience OFF so the audience itself is tested; interests cloned from historic
    West ad sets; end_time 12/3 09:00 +0800
  * spend_cap RM500 per campaign keeps the live within the operator's RM4,000 conversion budget
    (Broad A+ cap RM2,000 + interest × V1 RM472 spent + 3 × RM500)
  * built PAUSED. Idempotent by name.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_west_ab_nov as west  # noqa: E402
from build_west_ab_nov import throttle_tolerant  # noqa: E402

from adbot.commands import graph_client  # noqa: E402
from adbot.settings import load_settings  # noqa: E402

ACCT = west.ACCT
DAILY = 10000                          # RM100.00 per campaign (CBO)
SPEND_CAP = 50000                      # RM500.00 per campaign
END_TIME = "2026-12-03T09:00:00+0800"
ADS = [  # (ad name, existing creative) — the Broad A+ winners
    ("Video 5：飯桌生活細節場景", "2345501816295894"),
    ("Video 6：具體數字目標", "1462768695231750"),
    ("新馬 Video 7：14歲了，還有機會長高嗎", "1178236997968310"),
]
AUDIENCES = [  # (label, historic ad set to clone flexible_spec from)
    ("Parents 3-17 + Engaged", "120249101506230259"),
    ("Family and Relationships", "120235282642840259"),
    ("Food and Drink + Milk", "120235284875540259"),
]


def strip(flex):
    out = []
    for block in flex:
        nb = {}
        for k, items in block.items():
            if isinstance(items, list):
                nb[k] = [{"id": str(i["id"])} for i in items if isinstance(i, dict) and i.get("id")]
        if nb:
            out.append(nb)
    return out


def main() -> None:
    g = throttle_tolerant(graph_client(load_settings()))
    camps = {r["name"]: r["id"] for r in g._get_all(f"{ACCT}/campaigns", {"fields": "id,name", "limit": 500})}
    built = []
    for label, src in AUDIENCES:
        cname = f"US West | 州级 | CBO 1-1-3 | {label} | 12/2 live"
        cid = camps.get(cname) or g.create_campaign(
            ACCT, name=cname, objective="OUTCOME_SALES", buying_type="AUCTION", status="PAUSED",
            special_ad_categories=[], spend_cap=SPEND_CAP, daily_budget=DAILY,
            bid_strategy="LOWEST_COST_WITHOUT_CAP")["id"]
        print(f"== campaign {cid} {cname} ==", flush=True)
        time.sleep(2)
        flex = strip(g._request("GET", src, params={"fields": "targeting"})["targeting"].get("flexible_spec", []))
        n = sum(len(v) for b in flex for v in b.values())
        tgt = {"geo_locations": {"regions": west.RESOLVED_STATES, "location_types": ["home", "recent"]},
               "locales": [20, 21, 22], "excluded_custom_audiences": west.EXCLUDE,
               "age_min": 35, "age_max": 65, "targeting_automation": {"advantage_audience": 0},
               "flexible_spec": flex}
        aname = f"{label} | 州级 CA+WA | V5+V6+V7"
        have = {r["name"]: r["id"] for r in g._get_all(f"{cid}/adsets", {"fields": "id,name"})}
        asid = have.get(aname) or g.create_adset(
            ACCT, campaign_id=cid, name=aname, end_time=END_TIME,
            optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
            promoted_object={"pixel_id": west.PIXEL_ID, "custom_event_type": "COMPLETE_REGISTRATION"},
            targeting=tgt, status="PAUSED")["id"]
        print(f"  ad set {asid} {aname} ({n} targeting items from {src})", flush=True)
        time.sleep(3)
        have_ads = {r["name"] for r in g._get_all(f"{asid}/ads", {"fields": "id,name"})}
        for ad_name, crid in ADS:
            if ad_name in have_ads:
                print(f"    ad {ad_name} exists")
                continue
            adid = g.create_ad(ACCT, name=ad_name, adset_id=asid,
                               creative={"creative_id": crid}, status="PAUSED")["id"]
            print(f"    ad {adid} {ad_name}", flush=True)
            time.sleep(3)
        built.append(cid)
    print("== read-back ==")
    for cid in built:
        print("  campaign", g._request("GET", cid, params={
            "fields": "id,name,status,daily_budget,spend_cap,bid_strategy"}))
        for a in g._get_all(f"{cid}/adsets", {"fields": "id,name,status,end_time,targeting"}):
            t = a["targeting"]
            ads = g._get_all(f"{a['id']}/ads", {"fields": "id,name,status"})
            print(f"    {a['id']} {a['name']} [{a['status']} end {a.get('end_time')}] "
                  f"adv {t.get('targeting_automation')} age {t.get('age_min')}-{t.get('age_max')} "
                  f"flex {len(t.get('flexible_spec') or [])} ads {[(x['id'], x['name'], x['status']) for x in ads]}")
    print("DONE")


if __name__ == "__main__":
    main()
