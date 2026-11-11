"""Build the 8 new 馬丁醫師 videos for one US side: SIDE=em (default) or SIDE=west.

East+Midwest (live 2026-11-18, EST) built first; West added on operator request 2026-11-09
with the same structure, copy and names (West landing page /register, West pixel, West
城市级 F&R V1 targeting incl. its paid-list exclusions). For West the 8 videos already
uploaded to 美東美中 are attached by id (same business) — no re-upload; a video that the
account can't use falls back to a Drive download + upload.

Operator-approved 2026-11-09:
  1 new campaign  "US East+Midwest | 城市级 | F&R | 新影片 V1–V8"
  8 ad sets, one video each, ABO RM50/day (RM400/day total), built PAUSED.
  Targeting cloned from the existing 美東美中 "城市级 | Family and Relationships" V1 ad set
  (9 Doc cities + Toronto, Advantage+ audience ON, 15-day registrant exclusion) — the
  audience x geo cell that won the 11/4–11/12 West test.
  Per-video copy + headline + ad name: scripts/new8_copy.py (operator's script titles).
Videos are downloaded from Drive and uploaded to the 美東美中 account. New creatives
(page + IG martinyaoshi.us), LEARN_MORE to that side's landing page, standard UTM.
Idempotent by name; rules in docs/rules/us-weekly-funnel.md.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_em_ab_nov as em  # noqa: E402
import build_west_ab_nov as west  # noqa: E402
from build_west_ab_nov import throttle_tolerant  # noqa: E402
from new8_copy import VIDEOS  # noqa: E402

from adbot.commands import drive_client, graph_client  # noqa: E402
from adbot.settings import load_settings  # noqa: E402

SIDES = {
    "em": dict(mod=em, campaign="US East+Midwest | 城市级 | F&R | 新影片 V1–V8",
               template="US East+Midwest | 城市级 | Family and Relationships",
               prefix="Family and Relationships | 城市级 9 cities+Toronto | 新", reuse={}),
    "west": dict(mod=west, campaign="US West | 城市级 | F&R | 新影片 V1–V8",
                 template="US West | 城市级 | Family and Relationships",
                 prefix="Family and Relationships | 城市级 9 cities | 新",
                 # uploaded to 美東美中 by the 2026-11-09 EM run (lengths checked vs Drive)
                 reuse={1: "1479182944187498", 2: "1452701453491488", 3: "1004970651935400",
                        4: "2624501621402291", 5: "2636186750226231", 6: "2327068894794353",
                        7: "1128268050183585", 8: "2368479050560610"}),
    # operator 2026-11-11: East+Midwest history — all 3 paid sales came from Broad Advantage+
    # across the whole region, so the 8 new videos also go there (RM50 each). Targeting is
    # built (not cloned): 7 states + Ontario, no city exclusion, Advantage+ audience ON.
    "em_broad": dict(mod=em, campaign="US East+Midwest | Broad A+ | 新影片 V1–V8",
                     template=None,
                     prefix="Broad A+ | 7州+Ontario | 新",
                     reuse={1: "1479182944187498", 2: "1452701453491488", 3: "1004970651935400",
                            4: "2624501621402291", 5: "2636186750226231", 6: "2327068894794353",
                            7: "1128268050183585", 8: "2368479050560610"}),
}
SIDE = SIDES[os.environ.get("SIDE", "em").strip() or "em"]
M = SIDE["mod"]
ACCT = M.ACCT
CAMPAIGN = SIDE["campaign"]
TEMPLATE_CAMPAIGN = SIDE["template"]
ADSET_PREFIX = SIDE["prefix"]
DAILY = 5000                                  # RM50.00 per ad set
READ_ONLY_TARGETING = {"targeting_relaxation_types"}


def existing(g, edge, field="name"):
    return {r.get(field): r["id"] for r in g._get_all(f"{ACCT}/{edge}",
                                                       {"fields": f"id,{field}", "limit": 200})}


def upload(drive, g, v, dl):
    meta = drive._svc.files().get(fileId=v["drive_id"], fields="name",
                                  supportsAllDrives=True).execute()
    if meta["name"] != v["file"]:
        raise SystemExit(f"V{v['n']}: Drive file is '{meta['name']}', expected '{v['file']}'")
    path = dl / f"V{v['n']}.mp4"
    drive.download_file(v["drive_id"], path)
    print(f"  V{v['n']} downloaded {meta['name']} {path.stat().st_size/1e6:.1f}MB", flush=True)
    vid = g.upload_video(ACCT, str(path), v["ad_name"])
    path.unlink()
    print(f"  V{v['n']} uploaded video {vid}", flush=True)
    return vid


def make_creative(g, v, vid):
    vd = {"video_id": vid, "title": v["headline"], "message": v["body"],
          "call_to_action": {"type": "LEARN_MORE", "value": {"link": M.LINK}}}
    thumb = g.get_video_thumbnail(vid)
    if thumb:
        vd["image_url"] = thumb
    spec = {"page_id": M.PAGE_ID, "instagram_user_id": M.IG_USER_ID, "video_data": vd}
    return g.create_adcreative(ACCT, name=v["ad_name"], object_story_spec=spec,
                               url_tags=M.UTM)["id"]


def main() -> None:
    s = load_settings()
    g = throttle_tolerant(graph_client(s))

    print("== template targeting ==", flush=True)
    camps = existing(g, "campaigns")
    if TEMPLATE_CAMPAIGN is None:
        tgt = em.targeting({"geo": {"regions": em.STATE_REGIONS, "location_types": ["home", "recent"]},
                            "advantage": True, "exclude_geo": None}, {"flex": None})
        print("  built: 7 states + Ontario, no city exclusion, Advantage+ ON, Broad")
    else:
        tcid = camps.get(TEMPLATE_CAMPAIGN)
        if not tcid:
            raise SystemExit(f"template campaign not found: {TEMPLATE_CAMPAIGN}")
        tsets = g._get_all(f"{tcid}/adsets", {"fields": "id,name,targeting"})
        tmpl = next((a for a in tsets if a["name"].endswith("| V1")), None)
        if not tmpl:
            raise SystemExit(f"no V1 ad set in {TEMPLATE_CAMPAIGN}: {[a['name'] for a in tsets]}")
        tgt = {k: v for k, v in tmpl["targeting"].items() if k not in READ_ONLY_TARGETING}
        print(f"  cloning '{tmpl['name']}' ({tmpl['id']})")
    print(f"    geo       {json.dumps(tgt.get('geo_locations'), ensure_ascii=False)}")
    print(f"    advantage {tgt.get('targeting_automation')}  age {tgt.get('age_min')}-{tgt.get('age_max')}")
    print(f"    excl aud  {[x.get('id') for x in tgt.get('excluded_custom_audiences', [])]}")
    print(f"    interests {len((tgt.get('flexible_spec') or [{}])[0].get('interests', []))}", flush=True)

    print("== videos / creatives ==", flush=True)
    have_vid = existing(g, "advideos", "title")
    have_cr = existing(g, "adcreatives")
    dl = Path("/tmp/em_new8"); dl.mkdir(exist_ok=True)
    drive = drive_client(s)
    creative = {}
    for v in VIDEOS:
        if v["ad_name"] in have_cr:
            creative[v["n"]] = have_cr[v["ad_name"]]
            print(f"  V{v['n']} creative exists {creative[v['n']]}")
            continue
        vid = have_vid.get(v["ad_name"])
        if not vid and v["n"] in SIDE["reuse"]:
            rid = SIDE["reuse"][v["n"]]
            try:
                info = g._request("GET", rid, params={"fields": "id,length,status"})
                if (info.get("status") or {}).get("video_status") == "ready":
                    vid = rid
                    print(f"  V{v['n']} reusing uploaded video {rid} ({info.get('length')}s)", flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"  V{v['n']} video {rid} not usable here ({str(e)[:80]}) — uploading", flush=True)
        if not vid:
            vid = upload(drive, g, v, dl)
        try:
            creative[v["n"]] = make_creative(g, v, vid)
        except Exception as e:  # noqa: BLE001
            if vid != SIDE["reuse"].get(v["n"]):
                raise
            print(f"  V{v['n']} creative with reused video failed ({str(e)[:80]}) — uploading", flush=True)
            vid = upload(drive, g, v, dl)
            creative[v["n"]] = make_creative(g, v, vid)
        time.sleep(2)
        print(f"  V{v['n']} creative {creative[v['n']]}", flush=True)

    print("== campaign / ad sets / ads ==", flush=True)
    cid = camps.get(CAMPAIGN) or g.create_campaign(
        ACCT, name=CAMPAIGN, objective="OUTCOME_SALES", buying_type="AUCTION",
        status="PAUSED", special_ad_categories=[], is_adset_budget_sharing_enabled=False)["id"]
    print(f"  campaign {cid}  {CAMPAIGN}  (account {ACCT}, link {M.LINK})", flush=True)
    have_as = {r["name"]: r["id"] for r in g._get_all(f"{cid}/adsets", {"fields": "id,name"})}
    n_ads = 0
    for v in VIDEOS:
        asname = f"{ADSET_PREFIX}V{v['n']}"
        existed = asname in have_as
        asid = have_as.get(asname) or g.create_adset(
            ACCT, campaign_id=cid, name=asname, daily_budget=DAILY,
            bid_strategy="LOWEST_COST_WITHOUT_CAP",
            optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
            promoted_object={"pixel_id": M.PIXEL_ID, "custom_event_type": "COMPLETE_REGISTRATION"},
            targeting=tgt, status="PAUSED")["id"]
        time.sleep(3)
        have_ads = ({r["name"] for r in g._get_all(f"{asid}/ads", {"fields": "name"})}
                    if existed else set())
        if v["ad_name"] in have_ads:
            print(f"    {asid} {asname} (ad exists)")
            continue
        adid = g.create_ad(ACCT, name=v["ad_name"], adset_id=asid,
                           creative={"creative_id": creative[v["n"]]}, status="PAUSED")["id"]
        n_ads += 1
        time.sleep(3)
        print(f"    {asid} {asname} -> ad {adid} ({v['ad_name']})", flush=True)

    print("== read-back ==", flush=True)
    for a in g._get_all(f"{cid}/adsets", {"fields": "id,name,status,daily_budget"}):
        ads = g._get_all(f"{a['id']}/ads", {"fields": "id,name,status,creative{id,title,video_id}"})
        for ad in ads:
            cr = ad.get("creative", {})
            print(f"  {a['name']} [{a['status']} {a['daily_budget']}] -> {ad['name']} "
                  f"[{ad['status']}] creative {cr.get('id')}")
    print(f"DONE — {n_ads} new ads, all PAUSED")


if __name__ == "__main__":
    main()
