"""Add Video 2 and Video 10 to every US West A/B campaign (operator request 2026-11-06).

Each of the six "US West |" campaigns gets two more ad sets, one ad each:
  "<audience> | <geo tag> | V2" and "... | V10".
Targeting is cloned from the campaign's own V1 ad set, so geo, exclusions, interests and
the operator's Advantage+ choice (城市级 ON, 州级 OFF) stay identical within each cell.
Copy, headline, page, IG, link and UTM come from build_west_ab_nov.py. New posts (fresh
creatives), ABO RM50/day, built PAUSED. Idempotent by name.

Videos are the ones these ads ran with when they sold (lifetime West top-ads report):
  V2  "Video 2：我跟你说！"  video 899483189224414 (from creative 1307451824734956, Dec 2025)
  V10 "Video 10：如果你已經嘗試一切方法幫助孩子長高" video 2109908786525283
      (from creatives 1415830053354535 / 1275275161171216, Feb 2026)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_west_ab_nov as west  # noqa: E402

from adbot.commands import graph_client  # noqa: E402
from adbot.settings import load_settings  # noqa: E402

NEW = [
    {"key": "V2", "video_id": "899483189224414", "ad_name": "Video 2：我跟你说！"},
    {"key": "V10", "video_id": "2109908786525283",
     "ad_name": "Video 10：如果你已經嘗試一切方法幫助孩子長高"},
]
READ_ONLY_TARGETING = {"targeting_relaxation_types"}


def main() -> None:
    s = load_settings()
    g = west.throttle_tolerant(graph_client(s))
    acct = west.ACCT

    print("== creatives ==", flush=True)
    have_cr = west.existing(g, "adcreatives")
    creative = {}
    for v in NEW:
        if v["ad_name"] in have_cr:
            creative[v["key"]] = have_cr[v["ad_name"]]
            print(f"  {v['key']} creative exists {creative[v['key']]}")
            continue
        vd = {"video_id": v["video_id"], "title": west.HEADLINE, "message": west.BODY,
              "call_to_action": {"type": "LEARN_MORE", "value": {"link": west.LINK}}}
        thumb = g.get_video_thumbnail(v["video_id"])
        if thumb:
            vd["image_url"] = thumb
        spec = {"page_id": west.PAGE_ID, "instagram_user_id": west.IG_USER_ID, "video_data": vd}
        creative[v["key"]] = g.create_adcreative(acct, name=v["ad_name"],
                                                 object_story_spec=spec, url_tags=west.UTM)["id"]
        time.sleep(2)
        print(f"  {v['key']} creative {creative[v['key']]}", flush=True)

    print("== ad sets ==", flush=True)
    camps = {n: i for n, i in west.existing(g, "campaigns").items()
             if n and n.startswith("US West | ")}
    if len(camps) != 6:
        raise SystemExit(f"expected 6 US West campaigns, found {len(camps)}: {sorted(camps)}")
    n_ads = 0
    for cname, cid in sorted(camps.items()):
        sets = g._get_all(f"{cid}/adsets", {"fields": "id,name,targeting,daily_budget"})
        by_name = {a["name"]: a for a in sets}
        tmpl = next((a for a in sets if a["name"].endswith("| V1")), None)
        if not tmpl:
            raise SystemExit(f"no V1 ad set to clone in {cname}")
        prefix = tmpl["name"][: -len("V1")]
        tgt = {k: v for k, v in tmpl["targeting"].items() if k not in READ_ONLY_TARGETING}
        print(f"  {cname}: cloning targeting of '{tmpl['name']}' "
              f"(advantage {tgt.get('targeting_automation')}, age {tgt.get('age_min')}-{tgt.get('age_max')})",
              flush=True)
        for v in NEW:
            asname = prefix + v["key"]
            if asname in by_name:
                asid = by_name[asname]["id"]
                have_ads = {r["name"] for r in g._get_all(f"{asid}/ads", {"fields": "name"})}
            else:
                asid = g.create_adset(
                    acct, campaign_id=cid, name=asname, daily_budget=west.DAILY,
                    bid_strategy="LOWEST_COST_WITHOUT_CAP",
                    optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                    promoted_object={"pixel_id": west.PIXEL_ID,
                                     "custom_event_type": "COMPLETE_REGISTRATION"},
                    targeting=tgt, status="PAUSED")["id"]
                have_ads = set()
                time.sleep(3)
            if v["ad_name"] in have_ads:
                print(f"    {asid} {asname} (ad exists)")
                continue
            adid = g.create_ad(acct, name=v["ad_name"], adset_id=asid,
                               creative={"creative_id": creative[v["key"]]}, status="PAUSED")["id"]
            n_ads += 1
            time.sleep(3)
            print(f"    {asid} {asname} -> ad {adid}", flush=True)
    print(f"DONE — {n_ads} new ads, all PAUSED")


if __name__ == "__main__":
    main()
