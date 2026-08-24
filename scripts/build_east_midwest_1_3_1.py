"""One-off: build the US EAST + MIDWEST 1-3-1 ABO campaign for Video 2 (每年帶孩子去 check-up).

Operator request: 1 campaign · 3 ad sets (ABO, RM50/day each) · 1 ad each — same creative in
all three, so the AUDIENCE is the only variable:
  broad      — geo + age only, Advantage Audience on
  FR         — interest: Family & Relationships (real IDs cloned from live adset 120247153008970259)
  PE         — Parents 3-17 + Engaged (real IDs cloned from live adset 120247164684970259)

Region keys are resolved at run time from Meta's adgeolocation search (never guessed).
Downloads the Drive video, uploads it once, then builds the tree. Idempotent via state.
"""
from __future__ import annotations

import json
from pathlib import Path

from adbot import state
from adbot.commands import drive_client, graph_client
from adbot.logging import final_summary, get_logger
from adbot.settings import load_settings

US_ACCT = "act_921653460987535"   # 【美東美中】MTC X Martin New 6 (MYR)
PAGE_ID = "1180683238455992"
PIXEL_ID = "2035639583602118"     # 美東美中 US Martin Pixel (this account's own)
LINK = "https://kidsgrowthformula.com/webinar-main-page"
UTM = "utm_source={{adset.name}}&utm_medium={{placement}}&utm_campaign={{campaign.name}}&utm_content={{ad.name}}"
STATE_KEY = "entities_east_midwest_1_3_1_acct6"
DAILY_CENTS = 5000            # RM50.00/day per AD SET (ABO)
STATUS = "ACTIVE"

DRIVE_ID = "10QJAP56ClEeQhPWPYFONffPnPA9uVJ-V"
AD_NAME = "Video 2：每年帶孩子去 check-up"
CAMPAIGN_NAME = "US East+Midwest | Check-up 正常範圍 | 1-3-1 ABO"
HEADLINE = "🔴 醫生說「正常範圍」，不代表他長得夠快"

# 美東 + 美中 — Chinese-dense states in each region
EAST = ["New York", "New Jersey", "Massachusetts", "Pennsylvania",
        "Connecticut", "Maryland", "Virginia"]
MIDWEST = ["Illinois", "Michigan", "Ohio", "Minnesota"]

# This account has no custom audiences yet, and audience IDs are account-scoped — so there is
# nothing valid to exclude here. Left empty deliberately rather than copying the CA account's IDs.
EXCLUDE = []

CAPTION = """⚠️ 每年都帶孩子做 check-up，醫生每次都說：「他的身高還在正常範圍內。」

你就安心了。但你有沒有算過——他這一年，到底長了幾公分？

🗣️「醫生說沒問題啊。」
🗣️「他是晚長型，遲點就會抽高了。」
🗣️「我們家基因就這樣，沒辦法的。」

📉 可是幾個月過去、一年過去，孩子的身高好像還是停在那裡。每年只長 2、3 公分，甚至只有 1 公分。

👉 這裡有一個很多家長都忽略的關鍵：一次身高在正常範圍內，不代表他的成長速度沒有問題。

你真正要盯的，不是他現在幾公分，而是他這一年長了多少、速度有沒有慢下來。因為「正常範圍」是一條很寬的線，一個孩子可以在範圍內，同時整整兩年幾乎沒動。

所以除了那張 Growth Chart，你還需要看四件事：

🥣 每天吃進去的食物，適不適合他的體質？比如天天一杯牛奶當早餐，他的腸胃真的吸收得了嗎？

🌿 他是不是經常消化不良、容易過敏、排便不順，身體狀態一直沒有改善？

😴 他的睡眠夠不夠深、夠不夠穩？

🦵 他做的運動，是在幫身體長，還是只是讓他更累？筋膜和肌肉長期緊繃，身體其實很難往上長。

💔 而最讓我在意的是——很多北美的醫生會直接告訴家長：「華裔孩子的 DNA 本來就比較矮小，這是遺傳，很難改變。」

一句話，就把孩子的身高判了死刑。

👉 但基因決定的是起點，不是終點。遺傳可以被突破，而且沒有你想像中那麼難——前提是，你要先看得懂孩子現在卡在哪裡。

👨‍⚕️ 我是馬丁醫師，台灣執照醫師，中西醫結合背景，十多年來陪伴橫跨台灣、香港、新加坡、馬來西亞、美國、加拿大的華人家庭，一起找出孩子成長路上真正的卡點。

📘 這個星期，我有一堂免費線上課《兒童長高方程式》。我會帶你看懂：

📍 你的孩子到底還剩多少長高窗口期
📍 發育期的孩子，什麼該做、什麼絕對不能做
📍 怎麼從飲食、睡眠、運動和身體狀態，找出現在最該優先處理的地方

這堂課不能取代兒科醫生的診斷，但它能幫你更了解——什麼才是最適合你孩子的成長方案。

孩子 5 到 15 歲、每年都有做 check-up，卻還是只長 1 到 3 公分的家長，這堂課就是為你開的。

⏰ 名額有限，坐滿即止 👇 點擊下方連結，立即免費報名。

別讓「還在正常範圍內」這六個字，拖到窗口關上那一天——關了，就真的關了。"""


def resolve_regions(g, log, names):
    """Look up Meta region keys by state name — never guess geo IDs."""
    keys = []
    for q in names:
        res = g._request("GET", "search", params={
            "type": "adgeolocation", "location_types": json.dumps(["region"]),
            "q": q, "country_code": "US", "limit": 5})
        hit = next((r for r in res.get("data", [])
                    if (r.get("name") or "").lower() == q.lower()
                    and r.get("country_code") == "US"), None)
        if not hit:
            raise SystemExit(f"could not resolve region key for {q!r}")
        log.info("  region %-15s -> key %s", q, hit["key"])
        keys.append({"key": str(hit["key"])})
    return keys


def main() -> None:
    log = get_logger()
    s = load_settings()
    g = graph_client(s)

    st = state.load(STATE_KEY) or {}
    video_id = st.get("video_id")
    creative_id = st.get("creative_id")
    campaign_id = st.get("campaign_id")
    adsets = dict(st.get("adsets", {}))
    ads = dict(st.get("ads", {}))

    def persist():
        state.save(STATE_KEY, {"video_id": video_id, "creative_id": creative_id,
                               "campaign_id": campaign_id, "adsets": adsets, "ads": ads})

    log.info("resolving 美東 + 美中 region keys ...")
    regions = resolve_regions(g, log, EAST + MIDWEST)
    geo = {"regions": regions, "location_types": ["home", "recent"]}
    base = {"age_min": 25, "age_max": 65, "geo_locations": geo, "locales": [20, 21, 22]}
    if EXCLUDE:
        base["excluded_custom_audiences"] = EXCLUDE

    audiences = [
        {"key": "broad", "name": "Broad · East+Midwest · Advantage+",
         "targeting": {**base, "targeting_automation": {"advantage_audience": 1}}},
        {"key": "FR", "name": "interest: Family & Relationships",
         "targeting": {**base, "flexible_spec": [{"interests": [
             {"id": 6002991239659}, {"id": 6003101323797}, {"id": 6003232518610},
             {"id": 6003409392877}, {"id": 6003445506042}, {"id": 6003476182657},
             {"id": 6004100985609}]}],
             "targeting_automation": {"advantage_audience": 0}}},
        {"key": "PE", "name": "Parents 3-17 + Engaged",
         "targeting": {**base, "flexible_spec": [{
             "interests": [{"id": 6003263791114}, {"id": 6003346592981}],
             "behaviors": [{"id": 6071631541183}],
             "family_statuses": [{"id": 6023005529383}, {"id": 6023005570783},
                                 {"id": 6023005681983}, {"id": 6023080302983}]}],
             "targeting_automation": {"advantage_audience": 0}}},
    ]

    # 1) video: download from Drive + upload once
    if not video_id:
        dl = Path("/tmp/east_midwest")
        dl.mkdir(parents=True, exist_ok=True)
        path = dl / "v2_checkup.mp4"
        drive_client(s).download_file(DRIVE_ID, path)
        log.info("downloaded %s (%d bytes)", path, path.stat().st_size)
        video_id = g.upload_video(US_ACCT, str(path), AD_NAME)
        persist()
        log.info("uploaded video -> %s", video_id)

    # 2) creative (reused by all 3 ads)
    if not creative_id:
        video_data = {"video_id": video_id, "title": HEADLINE, "message": CAPTION,
                      "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
        thumb = g.get_video_thumbnail(video_id)
        if thumb:
            video_data["image_url"] = thumb
        creative_id = g.create_adcreative(
            US_ACCT, name=AD_NAME,
            object_story_spec={"page_id": PAGE_ID, "video_data": video_data},
            url_tags=UTM)["id"]
        persist()
        log.info("created creative %s", creative_id)

    # 3) campaign — ABO: no campaign budget, budget lives on each ad set
    if not campaign_id:
        campaign_id = g.create_campaign(
            US_ACCT, name=CAMPAIGN_NAME, objective="OUTCOME_SALES", buying_type="AUCTION",
            status=STATUS, special_ad_categories=[],
            # ABO: Meta requires this explicitly when there is no campaign budget. False keeps
            # each ad set's RM50 strictly its own, so the audience test stays clean.
            is_adset_budget_sharing_enabled=False)["id"]
        persist()
        log.info("created campaign %s (ABO)", campaign_id)

    # 4) 3 ad sets (RM50/day each) + 1 ad each
    summary = []
    for aud in audiences:
        ak = aud["key"]
        if ak not in adsets:
            adsets[ak] = g.create_adset(
                US_ACCT, campaign_id=campaign_id, name=aud["name"],
                daily_budget=DAILY_CENTS, bid_strategy="LOWEST_COST_WITHOUT_CAP",
                optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                promoted_object={"pixel_id": PIXEL_ID,
                                 "custom_event_type": "COMPLETE_REGISTRATION"},
                targeting=aud["targeting"], status=STATUS)["id"]
            persist()
            log.info("[%s] created ad set %s", ak, adsets[ak])
        if ak not in ads:
            ads[ak] = g.create_ad(US_ACCT, name=AD_NAME, adset_id=adsets[ak],
                                  creative={"creative_id": creative_id}, status=STATUS)["id"]
            persist()
            summary.append(f"  {ak:6} adset {adsets[ak]} -> ad {ads[ak]}")
            log.info("[%s] created ad %s", ak, ads[ak])

    log.info("=" * 60)
    for line in summary:
        log.info(line)
    final_summary(log, f"East+Midwest 1-3-1 ABO built ({STATUS}, RM50/day x 3 ad sets): "
                       f"campaign {campaign_id}, video {video_id}, creative {creative_id}, "
                       f"{len(ads)} ads.")


if __name__ == "__main__":
    main()
