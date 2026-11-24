"""US West 12/2 live — winning ad × different audiences (operator 2026-11-24).

Operator: 「這個是不是 winning ads try different ad sets？不開 advantage+」.
The West best seller (old V1 华人孩子在美国很难长高（双语）, ~20 of 44 West sales) goes into 5
interest ad sets — the interests behind most historic West sales (F&R 10, Fast Food 9,
Food & Drink + Milk 5, Cartoon 4, Business & Industry 4). Same video everywhere so only the
audience differs. Interests are cloned from the historic "CALIFORNIA - … - Dec 5" ad sets.
  * into the existing conversion campaign 120249369724880259 (its RM4,000 spend_cap covers all)
  * whole CA + WA, Chinese locales, registrants / paid lists excluded, age 35–65,
    Advantage+ audience OFF (operator's choice), RM50/day each, end_time 12/3 09:00 +0800
  * reuses the V1 creative already in the campaign; built PAUSED. Idempotent by name.
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
CAMPAIGN_ID = "120249369724880259"
V1_CREATIVE = "1474066187965527"
V1_AD_NAME = "Video 1：华人孩子在美国很难长高（双语）"
DAILY = 5000
END_TIME = "2026-12-03T09:00:00+0800"
SOURCES = [  # (ad set label, historic ad set to clone interests from)
    ("Family and Relationships", "120235282642840259"),
    ("Fast Food", "120235282599700259"),
    ("Food and Drink + Milk", "120235284875540259"),
    ("Cartoon", "120235276173260259"),
    ("Business & Industry", "120235284014140259"),
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
    have = {r["name"]: r["id"] for r in g._get_all(f"{CAMPAIGN_ID}/adsets", {"fields": "id,name"})}
    for label, src in SOURCES:
        name = f"{label} | 州级 CA+WA | V1"
        flex = strip(g._request("GET", src, params={"fields": "targeting"})["targeting"].get("flexible_spec", []))
        n = sum(len(v) for b in flex for v in b.values())
        tgt = {"geo_locations": {"regions": west.RESOLVED_STATES, "location_types": ["home", "recent"]},
               "locales": [20, 21, 22], "excluded_custom_audiences": west.EXCLUDE,
               "age_min": 35, "age_max": 65, "targeting_automation": {"advantage_audience": 0},
               "flexible_spec": flex}
        asid = have.get(name)
        if not asid:
            asid = g.create_adset(
                ACCT, campaign_id=CAMPAIGN_ID, name=name, daily_budget=DAILY, end_time=END_TIME,
                bid_strategy="LOWEST_COST_WITHOUT_CAP", optimization_goal="OFFSITE_CONVERSIONS",
                billing_event="IMPRESSIONS",
                promoted_object={"pixel_id": west.PIXEL_ID, "custom_event_type": "COMPLETE_REGISTRATION"},
                targeting=tgt, status="PAUSED")["id"]
            time.sleep(3)
            adid = g.create_ad(ACCT, name=V1_AD_NAME, adset_id=asid,
                               creative={"creative_id": V1_CREATIVE}, status="PAUSED")["id"]
            print(f"  {asid} {name} ({n} targeting items from {src}) -> ad {adid}", flush=True)
            time.sleep(3)
        else:
            print(f"  {asid} {name} exists")
    print("== read-back ==")
    for a in g._get_all(f"{CAMPAIGN_ID}/adsets", {"fields": "id,name,status,daily_budget,end_time,targeting"}):
        t = a["targeting"]
        ads = g._get_all(f"{a['id']}/ads", {"fields": "id,name,status"})
        print(f"  {a['id']} {a['name']} [{a['status']} {a['daily_budget']} end {a.get('end_time')}] "
              f"adv {t.get('targeting_automation')} age {t.get('age_min')}-{t.get('age_max')} "
              f"flex {len(t.get('flexible_spec') or [])} ads {[(x['id'], x['status']) for x in ads]}")
    print("DONE")


if __name__ == "__main__":
    main()
