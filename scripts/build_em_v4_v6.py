"""One-off: US East+Midwest — TWO campaigns, one per audience, one AD SET PER VIDEO.

Operator's requested shape (each creative isolated in its own ad set with its own budget, so
Meta cannot starve one creative in favour of another):

  Campaign A · Broad Advantage+          Campaign B · interest: Family & Relationships
    ad set -> V4  (RM50/day)               ad set -> V4  (RM50/day)
    ad set -> V6  (RM50/day)               ad set -> V6  (RM50/day)

Same two creatives in both campaigns: read across = audience test, read down = creative test.
Videos are uploaded ONCE and their creatives reused in both campaigns (creative_id is
account-scoped). Region keys resolved live from Meta's geo search. Built PAUSED for review.
"""
from __future__ import annotations

import json
from pathlib import Path

from adbot import state
from adbot.commands import drive_client, graph_client
from adbot.logging import final_summary, get_logger
from adbot.settings import load_settings

US_ACCT = "act_921653460987535"    # 【美東美中】MTC X Martin New 6 (MYR)
PAGE_ID = "1180683238455992"
PIXEL_ID = "2035639583602118"      # 美東美中 US Martin Pixel
LINK = "https://kidsgrowthformula.com/webinar-main-page"
UTM = "utm_source={{adset.name}}&utm_medium={{placement}}&utm_campaign={{campaign.name}}&utm_content={{ad.name}}"
STATE_KEY = "entities_em_v4_v6_two_campaigns"
DAILY_CENTS = 5000                 # RM50.00/day per AD SET
STATUS = "PAUSED"                  # operator reviews before it spends

# paid/registrant audience in THIS account
EXCLUDE = [{"id": "120254451454000558"}]   # [美東美中 US] 15days complete registration

EAST = ["New York", "New Jersey", "Massachusetts", "Pennsylvania",
        "Connecticut", "Maryland", "Virginia"]
MIDWEST = ["Illinois", "Michigan", "Ohio", "Minnesota"]


CAP_V4 = """🥛 在北美長大的華人孩子，看著洋人同學天天吃這個，長得又高又壯。

你家孩子，一樣吃——

卻比同學矮了一截。

同樣的早餐，為什麼差這麼多？

👉 問題不在食物。

是北美的飲食和生活方式，不適合我們華人孩子的體質。

🥐 牛奶、起司、麵包、冷食，天天當早餐。

🪑 上學坐、補習坐、回家對著螢幕又是坐。

😴 功課做到半夜，睡都睡不深。

華人孩子的腸胃本來就偏虛——這樣養下去，只會讓他越來越吸收不了。

💔 我知道你已經很努力了。

每天盯著他喝牛奶。

買最貴的長高保健品。

週末還送他去打球、拉單槓。

結果呢？他吃得比誰都多，身高就是不動。

你開始懷疑：是不是我們華人的基因，天生就矮人一截？

不是。

👉 營養要變成身高，得先過腸胃這一關。

腸胃卡住了，你補再多，也是白補。

所以重點從來不是「補得夠不夠」——

是他到底，吸不吸得進去。

📍 那你怎麼知道你的孩子有沒有這個問題？

今晚回家，自己檢查三件事，一分鐘就夠：

第一——他過去一年，是不是只長了一兩公分？

第二——他吃很多，卻不長肉、也不長高？

第三——他是不是經常鼻子過敏、皮膚癢、便秘，晚上睡不安穩？

三個全中——

這不是「在北美長大本來就比較慢」。

是他的吸收系統，在跟你求救。

👨‍⚕️ 我是馬丁醫師，來自台灣的兒童長高專家，超過 10 年中西醫整合經驗，已陪伴 7000+ 個華人家庭。

我的做法從來只有一句話：先健康，後長高。

不打針、不塞補品。

先把過敏壓下去、把腸胃調理好、讓他睡得夠深。

身體沒有負擔，吃進去的營養，才真正拿去長高。

⏳ 但我要老實跟你說一件事。

孩子的生長板一旦閉合，就再也長不高了。

到時候你花再多錢、買再貴的補品，都追不回來。

這不是嚇你，是時間的問題。

📘 我接下來有一堂免費的線上課程，我會直接告訴你：

📍 華人孩子在北美長不高的真正原因

📍 在生長板閉合之前，你還能為他做什麼

📍 怎麼從飲食、睡眠、腸胃，找出他現在最該調整的地方

⏰ 名額有限 👇 點擊下方連結，立即免費報名。

別讓孩子錯過長高黃金期，我們線上見。"""

CAP_V6 = """👨‍👧 我自己，也是一個爸爸。

換作是我的孩子長不高，我的第一件事，絕對不是急著買補品。

是先把他的腸胃和睡眠，顧好。

順序反了，補再多，都是白補。

💭 說實話，我會走上這一行，是因為我自己。

我小時候不矮——12 歲 165，13 歲就 173，一直是班上最高的那幾個。

我以為破 180，輕輕鬆鬆。

結果那年之後，我就再也沒長高過。

那個「本來可以更高」的遺憾，我放在心裡很多年。

所以我當上醫師以後，第一個一頭栽進去研究的，就是：孩子到底怎麼自然長高。

說白了——我不想讓下一個孩子，再走一次我的遺憾。

👉 後來我才發現，很多華人爸媽，順序都做反了。

一看到孩子矮，第一個動作就是「補」。

可是孩子如果一直過敏、腸胃不好、晚上睡不好——

你補進去的，他的身體用不上，全浪費掉。

所以要先做的，是把這些問題先解決。

先健康，再長高。真的有先後，不能顛倒。

👨‍⚕️ 我是馬丁醫師，台灣兒童長高專家，10 年中西醫整合經驗，已陪伴 7000+ 個華人家庭。

這十年，我就是用這個方法，陪過七千多個家庭。

很多爸媽自己也不高，孩子一樣一年一年往上長。

靠的不是什麼神奇補品，就是把順序擺對。

📘 這套順序、每一步該怎麼做，我整理成一堂免費的線上課程：

📍 為什麼「先補」是最常見也最貴的錯誤

📍 腸胃、睡眠、過敏，該先處理哪一個

📍 怎麼判斷你的孩子現在卡在哪一步

⏰ 名額有限 👇 點擊下方連結，立即免費報名。

一個爸爸，跟你說句真心話——

這條路，你不用自己一個人走。

我們線上見。"""

VIDEOS = [
    {"key": "V4", "drive_id": "1JZGlAHSuzlZJ6vFDSH535Fp1sBRatBI-",
     "ad_name": "Video 4：一樣的早餐，兩種身高",
     "slug": "V4 一樣的早餐",
     "headline": "🔴 一樣的早餐，為什麼你的孩子矮一截？",
     "caption": CAP_V4},
    {"key": "V6", "drive_id": "1mq6S9riYqMaF3xQCJLmmM6sl7bUiPwjC",
     "ad_name": "Video 6：我也是爸爸",
     "slug": "V6 我也是爸爸",
     "headline": "🔴 我也是爸爸——換作我的孩子，我不會先買補品",
     "caption": CAP_V6},
]


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
        keys.append({"key": str(hit["key"])})
    log.info("resolved %d region keys", len(keys))
    return keys


def main() -> None:
    log = get_logger()
    s = load_settings()
    g = graph_client(s)

    st = state.load(STATE_KEY) or {}
    videos = dict(st.get("videos", {}))        # key -> video_id
    creatives = dict(st.get("creatives", {}))  # key -> creative_id
    campaigns = dict(st.get("campaigns", {}))  # A/B -> campaign_id
    adsets = dict(st.get("adsets", {}))        # "A:V4" -> adset_id
    ads = dict(st.get("ads", {}))              # "A:V4" -> ad_id

    def persist():
        state.save(STATE_KEY, {"videos": videos, "creatives": creatives,
                               "campaigns": campaigns, "adsets": adsets, "ads": ads})

    regions = resolve_regions(g, log, EAST + MIDWEST)
    geo = {"regions": regions, "location_types": ["home", "recent"]}
    base = {"age_min": 25, "age_max": 65, "geo_locations": geo, "locales": [20, 21, 22],
            "excluded_custom_audiences": EXCLUDE}

    AUDIENCES = [
        {"key": "A", "campaign_name": "US East+Midwest | A · Broad Advantage+ | V4/V6",
         "adset_prefix": "Broad A+",
         # broad: geo + age only, Advantage Audience on — cheapest CPM in the last test
         "targeting": {**base, "targeting_automation": {"advantage_audience": 1}}},
        {"key": "B", "campaign_name": "US East+Midwest | B · Family & Relationships | V4/V6",
         "adset_prefix": "FR",
         # real interest IDs cloned from a live ad set — Meta ignores the name field
         "targeting": {**base, "flexible_spec": [{"interests": [
             {"id": 6002991239659}, {"id": 6003101323797}, {"id": 6003232518610},
             {"id": 6003409392877}, {"id": 6003445506042}, {"id": 6003476182657},
             {"id": 6004100985609}]}],
             "targeting_automation": {"advantage_audience": 0}}},
    ]

    # 1) upload each video ONCE + build one creative each (reused by both campaigns)
    dl = Path("/tmp/em_v4_v6")
    dl.mkdir(parents=True, exist_ok=True)
    for v in VIDEOS:
        k = v["key"]
        if k not in videos:
            path = dl / f"{k}.mp4"
            drive_client(s).download_file(v["drive_id"], path)
            log.info("[%s] downloaded %d bytes", k, path.stat().st_size)
            videos[k] = g.upload_video(US_ACCT, str(path), v["ad_name"])
            persist()
            log.info("[%s] uploaded video -> %s", k, videos[k])
        if k not in creatives:
            video_data = {"video_id": videos[k], "title": v["headline"], "message": v["caption"],
                          "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
            thumb = g.get_video_thumbnail(videos[k])
            if thumb:
                video_data["image_url"] = thumb
            creatives[k] = g.create_adcreative(
                US_ACCT, name=v["ad_name"],
                object_story_spec={"page_id": PAGE_ID, "video_data": video_data},
                url_tags=UTM)["id"]
            persist()
            log.info("[%s] created creative %s", k, creatives[k])

    # 2) two campaigns; inside each, ONE AD SET PER VIDEO with its own RM50
    summary = []
    for aud in AUDIENCES:
        ak = aud["key"]
        if ak not in campaigns:
            campaigns[ak] = g.create_campaign(
                US_ACCT, name=aud["campaign_name"], objective="OUTCOME_SALES",
                buying_type="AUCTION", status=STATUS, special_ad_categories=[],
                # ABO: required by Meta when there is no campaign budget. False keeps each ad
                # set's RM50 strictly its own, so no creative can starve another.
                is_adset_budget_sharing_enabled=False)["id"]
            persist()
            log.info("[%s] created campaign %s", ak, campaigns[ak])

        for v in VIDEOS:
            slot = f"{ak}:{v['key']}"
            if slot not in adsets:
                adsets[slot] = g.create_adset(
                    US_ACCT, campaign_id=campaigns[ak],
                    name=f"{aud['adset_prefix']} · {v['slug']}",
                    daily_budget=DAILY_CENTS, bid_strategy="LOWEST_COST_WITHOUT_CAP",
                    optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                    promoted_object={"pixel_id": PIXEL_ID,
                                     "custom_event_type": "COMPLETE_REGISTRATION"},
                    targeting=aud["targeting"], status=STATUS)["id"]
                persist()
                log.info("[%s] created ad set %s", slot, adsets[slot])
            if slot not in ads:
                ads[slot] = g.create_ad(US_ACCT, name=v["ad_name"], adset_id=adsets[slot],
                                        creative={"creative_id": creatives[v["key"]]},
                                        status=STATUS)["id"]
                persist()
                summary.append(f"  {slot:6} adset {adsets[slot]} -> ad {ads[slot]}")
                log.info("[%s] created ad %s", slot, ads[slot])

    log.info("=" * 60)
    for line in summary:
        log.info(line)
    final_summary(log, f"East+Midwest V4/V6 built ({STATUS}, RM50/day per ad set = RM200/day): "
                       f"campaign A {campaigns.get('A')}, campaign B {campaigns.get('B')}, "
                       f"{len(adsets)} ad sets, {len(ads)} ads.")


if __name__ == "__main__":
    main()
