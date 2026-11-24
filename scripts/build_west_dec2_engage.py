"""US West 12/2 live — engagement ads with Martin's IP (organic) videos (operator 2026-11-24).

Flow: engagement ad → viewer comments the video's keyword → ABC Sales AI (operator builds it,
connected to FB Page 馬丁藥師｜兒童身高管理專家 + IG martinyaoshi.us) DMs the free gift → 5 min
later DMs the webinar invite with a UTM-tagged /register link.
  * 4 videos (量身高三大誤區 dropped by the operator), one ad set each, RM38/day (RM152/day)
  * campaign spend_cap RM1,000 (operator: RM1,000 engagement for this live)
  * same targeting as the conversion campaign: whole CA + WA, Advantage+ ON, Chinese locales,
    registrants / paid lists excluded
  * new ad posts from the Drive videos (copied into the SA-readable California creatives
    folder 1lFIYt6Df9jdPu12lRn0R00ZKPMdnoT4z; the US IG copies have no keyword CTA)
Built PAUSED. Idempotent by name.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_west_ab_nov as west  # noqa: E402
from build_west_ab_nov import throttle_tolerant  # noqa: E402
from build_west_dec2 import targeting  # noqa: E402

from adbot.commands import drive_client, graph_client  # noqa: E402
from adbot.settings import load_settings  # noqa: E402

ACCT = west.ACCT
CAMPAIGN = "US West | 州级 | Engagement | 12/2 live"
SPEND_CAP = 100000                       # RM1,000.00
DAILY = 3800                             # RM38.00 per ad set
PREFIX = "Engagement A+ | 州级 CA+WA | "
TAGS = "\n\n#馬丁醫師 #孩子長高"

VIDEOS = [
    {"kw": "黑豆", "drive_id": "1nQrQGYv1gcf-UeK7jGv0sulqWHjHf0D5",
     "file": "IP Video：冬天有一杯東西 .mp4", "ad_name": "IP Video：冬天有一杯東西",
     "v2": True,   # operator rewrote the copy 2026-11-24 (verbatim below)
     "body": """冬天有一杯東西，比轉骨湯還重要 🍵

很多媽媽一到冬天，就幫孩子燉轉骨湯、買補品。
但補品不是每個孩子都適合，
沒有經過醫師或專業人員評估，不要自己給孩子吃。

天氣一冷，孩子手腳冰、晚上睡不沉，
吃進去的營養，很難真正用在長高上。

我把這杯的做法、份量和喝的時間，整理成一份小禮包。
想要的爸媽，留言「黑豆」，我私訊送給你 👇

#馬丁醫師 #孩子長高 #冬天 #黑豆"""},
    {"kw": "脾胃", "drive_id": "18dKqX2rG0wlZoIVQgu3h_rUDTAsiBcsh",
     "file": "IP Video：冬天常逼孩子多喝水？.mp4", "ad_name": "IP Video：冬天常逼孩子多喝水？",
     "body": """冬天常逼孩子多喝水？先停。

孩子嘴巴明明很乾，卻跟你說：我不渴。
很多時候，孩子不是缺水，是水卡住了。

脾胃管水的代謝，脾胃弱，水就流不到該去的地方。
孩子長高，不是靠硬灌，是靠吸收。

我整理了《冬天顧脾胃的5道甘苦早餐》，不含麥、不含奶，前一晚準備好，早上輕鬆上桌。
想要的爸媽，留言「脾胃」，我私訊給你 👇""" + TAGS + " #冬天 #脾胃"},
    {"kw": "原因", "drive_id": "1qR8DN2l44dsvWOhagYaY_buqWgsXQ2eN",
     "file": "IP Video：五個原因睡前喝牛奶長不高 .mp4", "ad_name": "IP Video：五個原因睡前喝牛奶長不高",
     "v2": True,   # operator rewrote the copy 2026-11-24 (verbatim below)
     "body": """睡前一杯牛奶，是很多爸媽每天都在做的事。
但這杯牛奶，可能正在偷走孩子長高的機會。

另外，我整理了很多家長最想知道的《長不高的5個原因》變成一份檢查表。
想要的爸媽，留言「原因」，我私訊給你 👇

#馬丁醫師 #孩子長高 #牛奶 #睡前"""},
    {"kw": "好眠", "drive_id": "1k9DWsVwXZzPz8SpNVwYnLibjAlFvky1F",
     "file": "IP Video：考試週怎麼長高？.mp4", "ad_name": "IP Video：考試週怎麼長高？",
     "body": """考試週，孩子讀到很晚，爸媽最擔心：睡少了，是不是就長不高？
成績和身高，從來不是二選一。

我把考試季會請家長做的睡前流程，整理成一份《考試週好眠清單》，
每一步都很簡單，今晚就能開始。
想要的爸媽，留言「好眠」，我私訊給你 👇""" + TAGS + " #考試週 #好眠"},
]


def existing(g, edge, field="name"):
    return {r.get(field): r["id"] for r in g._get_all(f"{ACCT}/{edge}",
                                                       {"fields": f"id,{field}", "limit": 200})}


def main() -> None:
    s = load_settings()
    g = throttle_tolerant(graph_client(s))
    tgt = targeting()
    print(f"== targeting ==\n  {json.dumps(tgt, ensure_ascii=False)}", flush=True)

    print("== videos / creatives ==", flush=True)
    have_vid = existing(g, "advideos", "title")
    have_cr = existing(g, "adcreatives")
    creative = {}
    for v in VIDEOS:
        if v.get("v2"):
            v["ad_name"] = v["ad_name"] + "｜v2"
    for v in VIDEOS:
        if v["ad_name"] in have_cr:
            creative[v["kw"]] = have_cr[v["ad_name"]]
            print(f"  {v['kw']}: creative exists {creative[v['kw']]}")
            continue
        vid = have_vid.get(v["ad_name"].replace("｜v2", ""))
        if not vid:
            drive = drive_client(s)
            meta = drive._svc.files().get(fileId=v["drive_id"], fields="name",
                                          supportsAllDrives=True).execute()
            if meta["name"] != v["file"]:
                raise SystemExit(f"{v['kw']}: Drive file is '{meta['name']}', expected '{v['file']}'")
            path = Path(f"/tmp/ip_{v['kw']}.mp4")
            drive.download_file(v["drive_id"], path)
            vid = g.upload_video(ACCT, str(path), v["ad_name"].replace("｜v2", ""))
            path.unlink()
            print(f"  {v['kw']}: uploaded {meta['name']} -> video {vid}", flush=True)
            for _ in range(30):
                st = (g._request("GET", vid, params={"fields": "status"}).get("status") or {})
                if st.get("video_status") == "ready":
                    break
                time.sleep(20)
        vd = {"video_id": vid, "message": v["body"]}
        thumb = g.get_video_thumbnail(vid)
        if thumb:
            vd["image_url"] = thumb
        spec = {"page_id": west.PAGE_ID, "instagram_user_id": west.IG_USER_ID, "video_data": vd}
        creative[v["kw"]] = g.create_adcreative(ACCT, name=v["ad_name"], object_story_spec=spec)["id"]
        print(f"  {v['kw']}: creative {creative[v['kw']]}", flush=True)
        time.sleep(2)

    print("== campaign / ad sets / ads ==", flush=True)
    cid = existing(g, "campaigns").get(CAMPAIGN) or g.create_campaign(
        ACCT, name=CAMPAIGN, objective="OUTCOME_ENGAGEMENT", buying_type="AUCTION",
        status="PAUSED", special_ad_categories=[], spend_cap=SPEND_CAP,
        is_adset_budget_sharing_enabled=False)["id"]
    print(f"  campaign {cid}  {CAMPAIGN}", flush=True)
    have_as = {r["name"]: r["id"] for r in g._get_all(f"{cid}/adsets", {"fields": "id,name"})}
    for v in VIDEOS:
        asname = PREFIX + v["kw"]
        existed = asname in have_as
        asid = have_as.get(asname) or g.create_adset(
            ACCT, campaign_id=cid, name=asname, daily_budget=DAILY,
            bid_strategy="LOWEST_COST_WITHOUT_CAP", destination_type="ON_POST",
            optimization_goal="POST_ENGAGEMENT", billing_event="IMPRESSIONS",
            targeting=tgt, status="PAUSED")["id"]
        time.sleep(3)
        have_ads = ({r["name"] for r in g._get_all(f"{asid}/ads", {"fields": "name"})}
                    if existed else set())
        if v["ad_name"] not in have_ads:
            adid = g.create_ad(ACCT, name=v["ad_name"], adset_id=asid,
                               creative={"creative_id": creative[v["kw"]]}, status="PAUSED")["id"]
            print(f"    {asid} {asname} -> ad {adid}", flush=True)
            time.sleep(3)
        else:
            print(f"    {asid} {asname} (ad exists)")

    print("== read-back ==")
    c = g._request("GET", cid, params={"fields": "name,status,spend_cap,objective"})
    print(f"  campaign {json.dumps(c, ensure_ascii=False)}")
    for a in g._get_all(f"{cid}/adsets", {"fields": "id,name,status,daily_budget,optimization_goal,destination_type"}):
        print(f"  {a['id']} {a['name']} [{a['status']} {a['daily_budget']} {a.get('optimization_goal')} {a.get('destination_type')}]")
        for ad in g._get_all(f"{a['id']}/ads", {"fields": "id,name,status,creative{id,effective_object_story_id}"}):
            print(f"      ad {ad['id']} {ad['name']} [{ad['status']}] creative {ad['creative']}")
    print("DONE — all PAUSED")


if __name__ == "__main__":
    main()
