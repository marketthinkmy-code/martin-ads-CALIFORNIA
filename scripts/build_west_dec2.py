"""US West rotation for the 12/2 live (PST) — operator-approved 2026-11-24.

Decisions (operator 2026-11-24, 「定 / 照建议 / RM50」):
  * geo = 州级 — whole California + Washington, cities INCLUDED (no city exclusion)
  * audience = Broad, Advantage+ audience ON (the East+Midwest winning cell)
  * 5 videos, one ad set each, ABO RM50/day (RM250/day), built PAUSED:
      old V1 华人孩子 (West's best seller, 20+ paid), 新V8, 新V5, 新V6, 新馬 V7
  * conversion budget for this live: RM4,000 → campaign spend_cap RM4,000 (hard ceiling)
Copy is the already-approved copy of each video (West V1 body; scripts/new8_copy.py;
scripts/newma5_copy.py for 新馬 V7). Existing West creatives are reused by name; 新馬 V7
gets a new creative (video uploaded from Drive). Idempotent by name.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_west_ab_nov as west  # noqa: E402
from build_west_ab_nov import throttle_tolerant  # noqa: E402
import new8_copy  # noqa: E402
import newma5_copy  # noqa: E402

from adbot.commands import drive_client, graph_client  # noqa: E402
from adbot.settings import load_settings  # noqa: E402

ACCT = west.ACCT
CAMPAIGN = "US West | 州级 | Broad A+ | 12/2 live"
SPEND_CAP = 400000                       # minor units: RM4,000.00
DAILY = 5000                             # RM50.00 per ad set
PREFIX = "Broad A+ | 州级 CA+WA | "

N8 = {v["n"]: v for v in new8_copy.VIDEOS}
NM = {v.get("tag"): v for v in newma5_copy.VIDEOS}
PLAN = [  # (ad set tag, ad name, copy source or None for reuse-only)
    ("V1", "Video 1：华人孩子在美国很难长高（双语）", None),
    ("新V8", N8[8]["ad_name"], N8[8]),
    ("新V5", N8[5]["ad_name"], N8[5]),
    ("新V6", N8[6]["ad_name"], N8[6]),
    ("新馬 V7", NM["V7"]["ad_name"], NM["V7"]),
]


def targeting():
    return {"geo_locations": {"regions": west.RESOLVED_STATES, "location_types": ["home", "recent"]},
            "locales": [20, 21, 22], "excluded_custom_audiences": west.EXCLUDE,
            "age_min": 25, "age_max": 65, "age_range": [35, 65],
            "targeting_automation": {"advantage_audience": 1}}


def existing(g, edge, field="name"):
    return {r.get(field): r["id"] for r in g._get_all(f"{ACCT}/{edge}",
                                                       {"fields": f"id,{field}", "limit": 200})}


def new_creative(g, s, v):
    have_vid = existing(g, "advideos", "title")
    vid = have_vid.get(v["ad_name"])
    if not vid:
        meta = drive_client(s)._svc.files().get(fileId=v["drive_id"], fields="name",
                                                supportsAllDrives=True).execute()
        if meta["name"] != v["file"]:
            raise SystemExit(f"Drive file is '{meta['name']}', expected '{v['file']}'")
        path = Path("/tmp/west_dec2.mp4")
        drive_client(s).download_file(v["drive_id"], path)
        vid = g.upload_video(ACCT, str(path), v["ad_name"])
        print(f"  uploaded {meta['name']} -> video {vid}", flush=True)
        for _ in range(30):
            st = (g._request("GET", vid, params={"fields": "status"}).get("status") or {})
            if st.get("video_status") == "ready":
                break
            time.sleep(20)
    vd = {"video_id": vid, "title": v["headline"], "message": v["body"],
          "call_to_action": {"type": "LEARN_MORE", "value": {"link": west.LINK}}}
    thumb = g.get_video_thumbnail(vid)
    if thumb:
        vd["image_url"] = thumb
    spec = {"page_id": west.PAGE_ID, "instagram_user_id": west.IG_USER_ID, "video_data": vd}
    return g.create_adcreative(ACCT, name=v["ad_name"], object_story_spec=spec,
                               url_tags=west.UTM)["id"]


def main() -> None:
    s = load_settings()
    g = throttle_tolerant(graph_client(s))
    tgt = targeting()
    print("== targeting ==")
    print(f"  {json.dumps(tgt, ensure_ascii=False)}", flush=True)

    print("== creatives ==", flush=True)
    have_cr = {n: i for n, i in existing(g, "adcreatives").items() if i not in west.STALE_CREATIVES}
    creative = {}
    for tag, ad_name, src in PLAN:
        if ad_name in have_cr:
            creative[tag] = have_cr[ad_name]
            print(f"  {tag}: reusing West creative {creative[tag]} ({ad_name})")
        elif src is None:
            raise SystemExit(f"{tag}: no existing West creative named {ad_name}")
        else:
            creative[tag] = new_creative(g, s, src)
            print(f"  {tag}: new creative {creative[tag]} ({ad_name})", flush=True)
        time.sleep(2)

    print("== campaign / ad sets / ads ==", flush=True)
    camps = existing(g, "campaigns")
    cid = camps.get(CAMPAIGN) or g.create_campaign(
        ACCT, name=CAMPAIGN, objective="OUTCOME_SALES", buying_type="AUCTION",
        status="PAUSED", special_ad_categories=[], spend_cap=SPEND_CAP,
        is_adset_budget_sharing_enabled=False)["id"]
    print(f"  campaign {cid}  {CAMPAIGN}", flush=True)
    have_as = {r["name"]: r["id"] for r in g._get_all(f"{cid}/adsets", {"fields": "id,name"})}
    for tag, ad_name, _ in PLAN:
        asname = PREFIX + tag
        existed = asname in have_as
        asid = have_as.get(asname) or g.create_adset(
            ACCT, campaign_id=cid, name=asname, daily_budget=DAILY,
            bid_strategy="LOWEST_COST_WITHOUT_CAP",
            optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
            promoted_object={"pixel_id": west.PIXEL_ID, "custom_event_type": "COMPLETE_REGISTRATION"},
            targeting=tgt, status="PAUSED")["id"]
        time.sleep(3)
        have_ads = ({r["name"] for r in g._get_all(f"{asid}/ads", {"fields": "name"})}
                    if existed else set())
        if ad_name not in have_ads:
            adid = g.create_ad(ACCT, name=ad_name, adset_id=asid,
                               creative={"creative_id": creative[tag]}, status="PAUSED")["id"]
            print(f"    {asid} {asname} -> ad {adid}", flush=True)
            time.sleep(3)
        else:
            print(f"    {asid} {asname} (ad exists)")

    print("== read-back ==")
    c = g._request("GET", cid, params={"fields": "name,status,spend_cap,objective"})
    print(f"  campaign {json.dumps(c, ensure_ascii=False)}")
    for a in g._get_all(f"{cid}/adsets", {"fields": "id,name,status,daily_budget,targeting"}):
        t = a["targeting"]
        print(f"  {a['id']} {a['name']} [{a['status']} {a['daily_budget']}] geo "
              f"{json.dumps(t.get('geo_locations'))} excl_geo {t.get('excluded_geo_locations')} "
              f"adv {t.get('targeting_automation')}")
        for ad in g._get_all(f"{a['id']}/ads", {"fields": "id,name,status,creative{id}"}):
            print(f"      ad {ad['id']} {ad['name']} [{ad['status']}] creative {ad['creative']['id']}")
    print("DONE — all PAUSED")


if __name__ == "__main__":
    main()
