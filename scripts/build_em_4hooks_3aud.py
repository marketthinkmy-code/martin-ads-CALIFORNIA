"""One-off: US East+Midwest — 3 audience campaigns x 4 videos, one ad set per video.

Operator shape: campaign = audience, ad set = one creative with its own RM50 so Meta cannot
starve a creative. Read across = audience test, read down = creative test.

  Parents 3-17 + Engaged        | Family and Relationships     | Food & Drink + Milk + Bread
    ad set -> Hook 1  RM50         ad set -> Hook 1  RM50          ad set -> Hook 1  RM50
    ad set -> Hook 2  RM50         ad set -> Hook 2  RM50          ad set -> Hook 2  RM50
    ad set -> Hook 6  RM50         ad set -> Hook 6  RM50          ad set -> Hook 6  RM50
    ad set -> Video 7 RM50         ad set -> Video 7 RM50          ad set -> Video 7 RM50

Each video is uploaded ONCE and its creative reused across all three campaigns. Region and
Food-interest IDs are resolved live from Meta search — never guessed. Built PAUSED.
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
STATE_KEY = "entities_em_4hooks_3audiences"
DAILY_CENTS = 5000                 # RM50.00/day per AD SET
STATUS = "PAUSED"
AGE_MIN, AGE_MAX = 35, 65

EXCLUDE = [{"id": "120254451454000558"}]   # [美東美中 US] 15days complete registration

EAST = ["New York", "New Jersey", "Massachusetts", "Pennsylvania",
        "Connecticut", "Maryland", "Virginia"]
MIDWEST = ["Illinois", "Michigan", "Ohio", "Minnesota"]

# Food & Drink + Milk + Bread — resolved live; operator will hand-tune this ad set afterwards.
FOOD_INTEREST_QUERIES = ["Food and drink", "Milk", "Bread", "Cooking", "Breakfast"]

CAP_H1 = """🔍 今晚回家，花一分鐘，檢查三件事——
你就知道孩子為什麼長不高。

第一：他過去一年，是不是只長了一兩公分？
第二：他吃很多，但是不長肉、也不長高？
第三：他是不是經常鼻子敏感、皮膚癢、便秘，晚上睡不安穩？

⚠️ 如果三個全中——
這不是「發育比較慢」。

是他的吸收系統，在跟你求救。

🗣️「多吃一點就會長啦。」
🗣️「男生晚長，再等等。」

👉 等，等不來身高。因為問題不在吃多少，在身體有沒有能力用。

我的做法，從來只有一句話：先健康，後長高。

❌ 不打針、不塞補品。
✅ 先把過敏壓下去、把腸胃修好、讓他睡得夠深——
身體沒有負擔了，吃進去的營養，才真正拿去長高。

但我要老實告訴你一件事：
⏳ 孩子的生長板一旦閉合，就再也長不高了。
到時候花再多錢、買再貴的東西，都追不回來。
這不是嚇你，是時間的問題。

👨‍⚕️ 我是馬丁醫師｜台灣兒童長高專家 · 中西醫整合經驗 10 年
已幫助超過 10,000 位孩子，破解「長不高」的問題。

我把整套方法，放進一堂免費的線上課程：

📍 三個信號背後，孩子長不高的底層原因是什麼
📍 過敏、腸胃、睡眠——先後順序怎麼排才對
📍 生長板閉合之前，你還可以為他做什麼

⏰ 名額有限，坐滿即止。

👇 點擊下方按鈕，立即免費報名。

今晚先檢查那三件事——
然後來上課，別讓孩子錯過長高黃金期。"""

CAP_H2 = """👟 孩子的鞋，是不是穿了一年多，還沒換大？

那你要小心了——
腳沒長，往往代表：他這一整年，都沒有什麼在長高。

我知道你已經很努力了。

🥛 每天逼他喝牛奶
💊 買最貴的保健品
🏃 逼他跳繩跳到膝蓋痛

📉 結果呢？他吃得比誰都多，身高就是不動。
你開始懷疑：是不是我們家基因就是這樣？

👉 不是。

營養要變成身高，得先過「腸胃」這一關。
腸胃卡住了，你補再多，也是白補。

重點從來不是補得夠不夠——
是他，吸不吸得進去。

怎麼知道你的孩子有沒有這個問題？
今晚回家，檢查三件事，一分鐘就夠：

📏 過去一年，是不是只長了一兩公分？
🍚 吃很多，但不長肉、也不長高？
🌿 經常鼻子敏感、皮膚癢、便秘，晚上睡不安穩？

⚠️ 三個全中——這是他的吸收系統在求救。

👨‍⚕️ 我是馬丁醫師｜台灣兒童長高專家 · 中西醫整合經驗 10 年
已幫助超過 10,000 位孩子破解「長不高」的問題。
我的做法只有一句話：先健康，後長高。不打針、不塞補品。

現在，我把整套方法放進一堂免費的線上課程：

📍 怎麼判斷孩子是「沒吃夠」還是「吸收不到」
📍 過敏、腸胃、睡眠的修復順序
📍 生長板閉合之前，你還來得及做的事

⏰ 名額有限，坐滿即止。

👇 點擊下方按鈕，立即免費報名。

一雙舊鞋，就能量出孩子這一年的成長——
別等鞋換大了才發現，時間已經過去了。"""

CAP_H6 = """⏳ 我告訴你一個數字，可能會嚇到你。

從孩子青春期啟動，到生長板閉合——
平均，只剩兩到三年。

🗣️「順其自然啦，大一點自己會抽高。」
🗣️「再等等看，他爸爸也是晚長的。」

😔 結果呢？很多家長，是等到孩子十五、十六歲，
突然不長了，才開始慌。

那時候才來找——說真的，剩下的時間，已經不多了。

👉 你要知道：長高，不是一條平平的直線。

它有一個黃金期。
青春期一啟動，倒數計時就開始跑了。

等那一波抽高結束、生長板一閉合，身高就定型。
這是骨頭的事，不是努力就能重來的事。

真正能幫孩子追高的，就是中間那短短幾年。

👨‍⚕️ 我是馬丁醫師｜台灣兒童長高專家 · 中西醫整合經驗 10 年
這十年，我幫助過超過 10,000 位孩子。
最讓我心疼的，永遠是同一種——
孩子明明還有空間，卻因為一句「再等等看」，白白錯過。

✅ 反過來，願意早一點看清楚狀況的，追回來的機會，大得多。

我把整套判斷方法，放進一堂免費的線上課程：

📍 怎麼判斷你的孩子，還剩多少長高時間
📍 黃金期裡，哪些事該做、哪些錢不該花
📍 用最健康的方式，把最後這段時間用對

⏰ 名額有限，坐滿即止。

👇 點擊下方按鈕，立即免費報名。

別再用一句「順其自然」，
賭掉孩子最後這幾年。"""

CAP_V7 = """我 13 歲，身高就有 173。

我以為，我隨便都能破 180——

📉 結果，從那一年開始，我就再也沒長高過。

我小時候不矮，在班上一直是最高的那幾個。
我爸媽也急。可那個年代，沒人懂查資料——

🥛 就只會叫我拼命喝牛奶、吃鈣片、燉補湯，帶我去看中醫調體質。

試了一整輪，我的身高，永遠停在 173。

173 不算矮。但我心裡一直有個遺憾：
如果當年有人教我對的方法，我很可能，不只停在這裡。

就是這個遺憾，讓我後來一頭栽進這一行——
我不想再有一個孩子，走一次我的冤枉路。

👉 後來我花了很多年才想通：
孩子長不高，不是缺哪一種補品。

是三件事沒做對。我把它叫「成長金三角」：

🔍 找出他長不高的體質原因
🔓 幫他打開身體的成長空間
🍽️ 配上真正適合這裡氣候的吃法

左邊那條路：喝牛奶、吃鈣片、燉補湯、亂買保健品——錢花了，時間也沒了。
右邊這三步，才是真正該走的順序。

👨‍⚕️ 我是馬丁醫師｜台灣兒童長高專家 · 中西醫整合經驗 10 年
這十年，我用這套「成長金三角」，幫助過超過 10,000 位孩子。
很多爸媽自己也不高，孩子一樣一年一年穩穩往上長。

這套金三角到底怎麼一步步做，
我完整講給你聽——就在一堂免費的線上課程裡：

📍 第一步：怎麼找出孩子長不高的體質原因
📍 第二步：怎麼打開身體的成長空間
📍 第三步：三餐怎麼配，營養才留得住

⏰ 名額有限，坐滿即止。

👇 點擊下方按鈕，立即免費報名。

我不想你跟我一樣，多年以後才在後悔——
「早知道，就好了。」"""



VIDEOS = [
    {"key": "H1", "drive_id": "1YAeiSjwB-2eb_-zs5lJFIO15jGdFi_NC",
     "ad_name": "Hook 1：今晚回家檢查三件事",
     "headline": "🔴 今晚回家，檢查這三件事", "caption": CAP_H1},
    {"key": "H2", "drive_id": "1bxY0AK0hWJdVJKiElp1vNotEIWY-dqK4",
     "ad_name": "Hook 2：舊鞋當尺",
     "headline": "🔴 孩子的鞋，一年沒換大？", "caption": CAP_H2},
    {"key": "H6", "drive_id": "1fBF7qq9eKLOX6OpeocvwRrwxNk2D6by9",
     "ad_name": "Hook 6：只剩兩到三年",
     "headline": "🔴 平均只剩兩到三年，你知道嗎", "caption": CAP_H6},
    {"key": "V7", "drive_id": "162Aes_btHX2pFo3K9TOzu7Nw5wV5qQ9J",
     "ad_name": "Video 7：我13歲身高173",
     "headline": "🔴 我 13 歲 173，然後再也沒長過", "caption": CAP_V7},
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


def resolve_interests(g, log, queries):
    """Resolve interest names to real Meta IDs via adinterest search (Meta ignores the name)."""
    out, seen = [], set()
    for q in queries:
        res = g._request("GET", "search", params={"type": "adinterest", "q": q, "limit": 5})
        rows = res.get("data", [])
        hit = next((r for r in rows if (r.get("name") or "").lower() == q.lower()), None)
        if not hit and rows:
            hit = rows[0]           # fall back to Meta's own top match
        if not hit:
            log.warning("no interest match for %r — skipping", q)
            continue
        if hit["id"] in seen:
            continue
        seen.add(hit["id"])
        out.append({"id": hit["id"]})
        log.info("  interest %-16s -> %s (%s)", q, hit["id"], hit.get("name"))
    if not out:
        raise SystemExit("could not resolve any Food & Drink interests")
    return out


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

    log.info("resolving Food & Drink interests ...")
    food_interests = resolve_interests(g, log, FOOD_INTEREST_QUERIES)

    AUDIENCES = [
        {"key": "PE", "name": "Parents 3-17 + Engaged",
         "campaign_name": "US East+Midwest | Parents 3-17 + Engaged | 4 hooks",
         # real IDs cloned from a live ad set
         "targeting": {**base, "flexible_spec": [{
             "interests": [{"id": 6003263791114}, {"id": 6003346592981}],
             "behaviors": [{"id": 6071631541183}],
             "family_statuses": [{"id": 6023005529383}, {"id": 6023005570783},
                                 {"id": 6023005681983}, {"id": 6023080302983}]}]}},
        {"key": "FR", "name": "Family and Relationships",
         "campaign_name": "US East+Midwest | Family and Relationships | 4 hooks",
         "targeting": {**base, "flexible_spec": [{"interests": [
             {"id": 6002991239659}, {"id": 6003101323797}, {"id": 6003232518610},
             {"id": 6003409392877}, {"id": 6003445506042}, {"id": 6003476182657},
             {"id": 6004100985609}]}]}},
        {"key": "FD", "name": "Food & Drink + Milk + Bread",
         "campaign_name": "US East+Midwest | Food & Drink + Milk + Bread | 4 hooks",
         "targeting": {**base, "flexible_spec": [{"interests": food_interests}]}},
    ]

    # 1) upload each video ONCE + one creative each, reused by all three campaigns
    dl = Path("/tmp/em_4hooks")
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
    final_summary(log, f"East+Midwest 4 hooks x 3 audiences built ({STATUS}, RM50/day per ad set "
                       f"= RM600/day): campaigns {list(campaigns.values())}, "
                       f"{len(adsets)} ad sets, {len(ads)} ads.")


if __name__ == "__main__":
    main()
