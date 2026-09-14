"""One-off: US East+Midwest — V3 + 4 北美 hooks across two audience campaigns.

Shape the operator asked for: campaign = audience, ad set = ONE creative with its own RM50,
so Meta cannot starve a creative. Read across = audience test, read down = creative test.

  Parents 3-17 + Engaged          Family and Relationships
    ad set -> V3  RM50              ad set -> V3  RM50
    ad set -> H3  RM50              ad set -> H3  RM50
    ad set -> H4  RM50              ad set -> H4  RM50
    ad set -> H5  RM50              ad set -> H5  RM50
    ad set -> H6  RM50              ad set -> H6  RM50

Each video is uploaded ONCE and its creative reused in both campaigns. Region keys resolved
live from Meta search — never guessed. Ad sets are named after the targeting, per house rule.
Built PAUSED.
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
LINK = "https://kidsgrowthformula.com/us-register"
UTM = "utm_source={{adset.name}}&utm_medium={{placement}}&utm_campaign={{campaign.name}}&utm_content={{ad.name}}"
STATE_KEY = "entities_em_v3_h3456"
DAILY_CENTS = 5000                 # RM50.00/day per AD SET
STATUS = "PAUSED"
AGE_MIN, AGE_MAX = 35, 65

EXCLUDE = [{"id": "120254451454000558"}]   # [美東美中 US] 15days complete registration

EAST = ["New York", "New Jersey", "Massachusetts", "Pennsylvania",
        "Connecticut", "Maryland", "Virginia"]
MIDWEST = ["Illinois", "Michigan", "Ohio", "Minnesota"]

CAP_V3 = """🇺🇸 家長們，你有沒有發現？
在美國長大的華人孩子，從小很容易出現一種隱藏的自卑感。

不是成績不好。
而是——「為什麼別的同學好像都比我高？」

🏀 在美國校園裡，體育文化非常強。
很多孩子從小就在運動，身形優勢越來越明顯。
當你的孩子站在人群裡，發現自己比同齡人矮一點的時候，
😔 他可能會開始懷疑：「是不是因為我是亞洲人，所以我天生就比較矮？」

🗣️「多喝牛奶就好了啦。」
🗣️「亞洲人本來就這樣。」

👉 很多華人父母第一個反應就是：補鈣、買 supplement、安排更多運動。
但很多時候，問題不是補得不夠，
而是孩子的身體，還沒有準備好成長。
基因決定的是一個範圍，後天的身體狀態，才決定他能不能發揮這個範圍。

📍 尤其是三件很多父母一直忽略的事：
他每天睡得夠，但真的睡得深嗎？
他每天吃很多，但腸胃真的吸收得好嗎？
他長期鼻子過敏，會不會正在消耗他的身體？

這三件事，才是我每次評估孩子成長時，最先看的重點。

👨‍⚕️ 我是馬丁醫師｜台灣兒童長高專家 · 中西醫整合經驗 10 年
已幫助超過 10,000 位孩子，破解「長不高」的問題。

我把整套判斷方法，放進一堂免費的線上課程：
📍 怎麼從睡眠、腸胃、過敏，判斷影響成長的關鍵因素
📍 孩子現在最該優先調整的是哪一項
📍 生長板閉合之前，你還可以為他做什麼

⏰ 名額有限，坐滿即止。
👇 點擊下方按鈕，立即免費報名。

別等孩子到了青春期後期，才發現成長空間越來越有限。"""

CAP_H3 = """📏 很多爸媽，一年幫孩子量一次身高。
越量越焦慮——因為那個數字，幾乎沒動。

👉 但真正的問題，不在這條尺上。
是在他身體裡面。

💔 我知道你已經很努力了。
每天盯著他喝牛奶、買最貴的長高保健品，
週末還送他去打球、拉單槓。

📉 結果呢？他吃得比誰都多，身高就是不動。
你開始懷疑：是不是我們華人的基因，天生就矮人一截？

👉 不是。
營養要變成身高，得先過「腸胃」這一關。
腸胃卡住了，你補再多，也是白補。
重點從來不是補得夠不夠——是他，吸不吸得進去。

📍 今晚回家，檢查三件事，一分鐘就夠：
他過去一年，是不是只長了一兩公分？
他吃很多，卻不長肉、也不長高？
他是不是經常鼻子過敏、皮膚癢、便秘，晚上睡不安穩？

⚠️ 三個全中——這是他的吸收系統在跟你求救。

👨‍⚕️ 我是馬丁醫師｜台灣兒童長高專家 · 中西醫整合經驗 10 年
已幫助超過 10,000 位孩子，破解「長不高」的問題。
我的做法只有一句話：先健康，後長高。

❌ 不打針、不塞補品。
✅ 先把過敏壓下去、把腸胃修好、讓他睡得夠深。

我把整套方法，放進一堂免費的線上課程：
📍 怎麼判斷孩子是「沒吃夠」還是「吸收不到」
📍 過敏、腸胃、睡眠的修復順序
📍 生長板閉合之前，你還來得及做的事

⏰ 名額有限，坐滿即止。
👇 點擊下方按鈕，立即免費報名。

別再一年量一次、焦慮一次——這次，換個地方找答案。"""

CAP_H4 = """💊 這種東西，我常常叫家長直接丟掉。
不是它沒用——是你孩子的身體，現在根本吸收不了。
⚠️ 你買得越貴，可能只是越幫倒忙。

👉 營養要變成身高，得先過「腸胃」這一關。
腸胃卡住了，你補再多，也是白補。
所以重點從來不是「補得夠不夠」——
是他到底，吸不吸得進去。

🗣️「那我是不是買錯牌子？」
🗣️「要不要換更貴的？」

👉 都不是。是順序做反了。

📍 今晚回家，先檢查三件事，一分鐘就夠：
他過去一年，是不是只長了一兩公分？
他吃很多，卻不長肉、也不長高？
他是不是經常鼻子過敏、皮膚癢、便秘，晚上睡不安穩？

⚠️ 三個全中——先別再買下一罐了。
那不是缺補品，是吸收系統在求救。

👨‍⚕️ 我是馬丁醫師｜台灣兒童長高專家 · 中西醫整合經驗 10 年
已幫助超過 10,000 位孩子，破解「長不高」的問題。
我的做法只有一句話：先健康，後長高。

❌ 不打針、不塞補品。
✅ 先把過敏壓下去、把腸胃修好、讓他睡得夠深——
身體沒有負擔了，吃進去的營養才真正拿去長高。

我把整套方法，放進一堂免費的線上課程：
📍 為什麼「先補」是最常見也最貴的錯誤
📍 過敏、腸胃、睡眠，該先處理哪一個
📍 什麼情況下，補品才真的有意義

⏰ 名額有限，坐滿即止。
👇 點擊下方按鈕，立即免費報名。

在買下一罐之前，先花一堂課的時間，搞清楚他到底卡在哪。"""

CAP_H5 = """🧬 你跟你另一半都不高，就認定孩子這輩子矮定了？
錯。
基因只決定範圍，決定不了他最後長到哪。

💔 我知道你已經很努力了。
每天盯著他喝牛奶、買最貴的長高保健品，
週末還送他去打球、拉單槓。

📉 結果呢？他吃得比誰都多，身高就是不動。
於是你更確定了：一定是基因。

👉 但你有沒有想過另一個可能——
不是他沒吃夠，是他的身體用不上。
營養要變成身高，得先過「腸胃」這一關。
腸胃卡住了，你補再多也是白補。

📍 今晚回家，檢查三件事，一分鐘就夠：
他過去一年，是不是只長了一兩公分？
他吃很多，卻不長肉、也不長高？
他是不是經常鼻子過敏、皮膚癢、便秘，晚上睡不安穩？

⚠️ 三個全中——那就不是基因的問題，是吸收系統在跟你求救。

👨‍⚕️ 我是馬丁醫師｜台灣兒童長高專家 · 中西醫整合經驗 10 年
已幫助超過 10,000 位孩子，破解「長不高」的問題。

✅ 我看過太多爸媽自己也不高，孩子一樣一年一年穩穩往上長。
靠的不是神奇補品，是把順序做對：先健康，後長高。

我把整套方法，放進一堂免費的線上課程：
📍 基因到底決定了什麼、沒決定什麼
📍 過敏、腸胃、睡眠的修復順序
📍 生長板閉合之前，你還來得及做的事

⏰ 名額有限，坐滿即止。
👇 點擊下方按鈕，立即免費報名。

別太早幫孩子的身高下結論——
那句「我們家基因就這樣」，可能是最虧他的一句話。"""

CAP_H6 = """📸 班級大合照，你一眼就找到你的孩子——
因為他總是站在最前排、最矮的那一個。

🗣️ 你嘴上說順其自然，心裡其實很急。
我懂。這件事，真的還有得救。

💔 我知道你已經很努力了。
每天盯著他喝牛奶、買最貴的長高保健品，
週末還送他去打球、拉單槓。

📉 結果呢？他吃得比誰都多，身高就是不動。
你開始懷疑：是不是我們華人的基因，天生就矮人一截？

👉 不是。
營養要變成身高，得先過「腸胃」這一關。
腸胃卡住了，你補再多也是白補。
重點從來不是補得夠不夠，是他吸不吸得進去。

📍 今晚回家，檢查三件事，一分鐘就夠：
他過去一年，是不是只長了一兩公分？
他吃很多，卻不長肉、也不長高？
他是不是經常鼻子過敏、皮膚癢、便秘，晚上睡不安穩？

⚠️ 三個全中——這是他的吸收系統在跟你求救。

👨‍⚕️ 我是馬丁醫師｜台灣兒童長高專家 · 中西醫整合經驗 10 年
已幫助超過 10,000 位孩子，破解「長不高」的問題。
我的做法只有一句話：先健康，後長高。

❌ 不打針、不塞補品。
✅ 先把過敏壓下去、把腸胃修好、讓他睡得夠深。

我把整套方法，放進一堂免費的線上課程：
📍 三個信號背後，孩子長不高的底層原因
📍 過敏、腸胃、睡眠，先後順序怎麼排才對
📍 生長板閉合之前，你還可以為他做什麼

⏰ 名額有限，坐滿即止。
👇 點擊下方按鈕，立即免費報名。

下一張班級合照，我希望你找他的時候，要多看兩眼才找得到。"""



VIDEOS = [
    {"key": "V3", "drive_id": "11sTk4iWxPzAjgVLWo3FPgLKP_Db2xWmr",
     "ad_name": "Video 3：身高影響自信",
     "headline": "🔴 身高影響的，不只是身高", "caption": CAP_V3},
    {"key": "H3", "drive_id": "1-3zQy23RkXvqbaw7aKQC35GhQWFu1p9b",
     "ad_name": "北美 Hook 3：卷尺越量越焦慮",
     "headline": "🔴 越量越焦慮，問題不在那條尺", "caption": CAP_H3},
    {"key": "H4", "drive_id": "1Gyz5CyouzH5IMgDfld5p_XZ_N8fF25iV",
     "ad_name": "北美 Hook 4：保健品叫你丟掉",
     "headline": "🔴 這種東西，我常叫家長直接丟掉", "caption": CAP_H4},
    {"key": "H5", "drive_id": "1cCW8PpfP2mQ2tKQkEnP8TOeEfgYvgsUi",
     "ad_name": "北美 Hook 5：基因打臉",
     "headline": "🔴 基因只決定範圍，不決定終點", "caption": CAP_H5},
    {"key": "H6", "drive_id": "1MwyKx7cIzeRssWMWZxjCsTwTntr_JzwC",
     "ad_name": "北美 Hook 6：最矮的那一個",
     "headline": "🔴 班級合照，他總是最矮的那一個", "caption": CAP_H6},
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
    videos = dict(st.get("videos", {}))
    creatives = dict(st.get("creatives", {}))
    campaigns = dict(st.get("campaigns", {}))
    adsets = dict(st.get("adsets", {}))
    ads = dict(st.get("ads", {}))

    def persist():
        state.save(STATE_KEY, {"videos": videos, "creatives": creatives,
                               "campaigns": campaigns, "adsets": adsets, "ads": ads})

    regions = resolve_regions(g, log, EAST + MIDWEST)
    geo = {"regions": regions, "location_types": ["home", "recent"]}
    base = {"age_min": AGE_MIN, "age_max": AGE_MAX, "geo_locations": geo,
            "locales": [20, 21, 22], "excluded_custom_audiences": EXCLUDE,
            "targeting_automation": {"advantage_audience": 0}}

    AUDIENCES = [
        {"key": "PE", "name": "Parents 3-17 + Engaged",
         "campaign_name": "US East+Midwest | Parents 3-17 + Engaged | V3+H3456",
         # real IDs cloned from a live ad set — Meta ignores the name field
         "targeting": {**base, "flexible_spec": [{
             "interests": [{"id": 6003263791114}, {"id": 6003346592981}],
             "behaviors": [{"id": 6071631541183}],
             "family_statuses": [{"id": 6023005529383}, {"id": 6023005570783},
                                 {"id": 6023005681983}, {"id": 6023080302983}]}]}},
        {"key": "FR", "name": "Family and Relationships",
         "campaign_name": "US East+Midwest | Family and Relationships | V3+H3456",
         "targeting": {**base, "flexible_spec": [{"interests": [
             {"id": 6002991239659}, {"id": 6003101323797}, {"id": 6003232518610},
             {"id": 6003409392877}, {"id": 6003445506042}, {"id": 6003476182657},
             {"id": 6004100985609}]}]}},
    ]

    # 1) upload each video ONCE + one creative each, reused by both campaigns
    dl = Path("/tmp/em_v3_h3456")
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

    # 2) one campaign per audience; one ad set per video inside it
    summary = []
    for aud in AUDIENCES:
        ak = aud["key"]
        if ak not in campaigns:
            campaigns[ak] = g.create_campaign(
                US_ACCT, name=aud["campaign_name"], objective="OUTCOME_SALES",
                buying_type="AUCTION", status=STATUS, special_ad_categories=[],
                # ABO: Meta requires this when there is no campaign budget. False keeps each ad
                # set's RM50 strictly its own.
                is_adset_budget_sharing_enabled=False)["id"]
            persist()
            log.info("[%s] created campaign %s", ak, campaigns[ak])

        for v in VIDEOS:
            slot = f"{ak}:{v['key']}"
            if slot not in adsets:
                adsets[slot] = g.create_adset(
                    US_ACCT, campaign_id=campaigns[ak], name=aud["name"],
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
                summary.append(f"  {slot:8} adset {adsets[slot]} -> ad {ads[slot]}")
                log.info("[%s] created ad %s", slot, ads[slot])

    log.info("=" * 60)
    for line in summary:
        log.info(line)
    final_summary(log, f"East+Midwest V3+H3/H4/H5/H6 built ({STATUS}, RM50/day per ad set "
                       f"= RM500/day): campaigns {list(campaigns.values())}, "
                       f"{len(adsets)} ad sets, {len(ads)} ads.")


if __name__ == "__main__":
    main()
