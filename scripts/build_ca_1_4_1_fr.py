"""One-off: 1-4-1 ABO in the CALIFORNIA account — 4 North America videos, one per ad set.

Operator request: all 4 videos from the 北美 Drive folder, each in its OWN ad set, every ad set
targeting the same audience (interest: Family & Relationships), ABO RM50/day each.
So the CREATIVE is the only variable across ad sets — a clean 4-way creative test.

Captions: V2 (check-up) and V5 (倒數計時) reuse the copy already written and shipped; SV1 (早餐)
and V1 (身體很累了) are newly written from their scripts. Idempotent via state.
"""
from __future__ import annotations

import json
from pathlib import Path

from adbot import state
from adbot.commands import drive_client, graph_client
from adbot.logging import final_summary, get_logger
from adbot.settings import load_settings

US_ACCT = "act_1629566827721449"   # 【加州】MTC X Martin New 5
PAGE_ID = "1180683238455992"
PIXEL_ID = "1921735088376759"
LINK = "https://kidsgrowthformula.com/us-register"
UTM = "utm_source={{adset.name}}&utm_medium={{placement}}&utm_campaign={{campaign.name}}&utm_content={{ad.name}}"
STATE_KEY = "entities_ca_1_4_1_fr"
DAILY_CENTS = 5000                 # RM50.00/day per AD SET (ABO)
STATUS = "ACTIVE"
CAMPAIGN_NAME = "CA | Family & Relationships | 1-4-1 ABO (北美 4 videos)"

GEO = {"regions": [{"key": "3847"}, {"key": "3871"}, {"key": "3880"}, {"key": "3890"}],
       "location_types": ["home", "recent"]}
EXCLUDE = [{"id": "120236056842490259"}, {"id": "120240867576290259"}, {"id": "120243775674560259"}]

# interest: Family & Relationships — real IDs cloned from live adset 120247153008970259
TARGETING = {
    "age_min": 25, "age_max": 65, "geo_locations": GEO, "locales": [20, 21, 22],
    "flexible_spec": [{"interests": [
        {"id": 6002991239659}, {"id": 6003101323797}, {"id": 6003232518610},
        {"id": 6003409392877}, {"id": 6003445506042}, {"id": 6003476182657},
        {"id": 6004100985609}]}],
    "excluded_custom_audiences": EXCLUDE,
    "targeting_automation": {"advantage_audience": 0},
}

CAP_SV1 = """🍞 你還在給孩子吃麵包、pancake 當早餐嗎？再配一杯牛奶、oat milk，或是一盒 yogurt？

如果是——那先別急著怪他長不高。

😣 你有沒有發現，他常常鼻子過敏、皮膚癢、肚子不舒服、排便也不順？

👉 在中醫的角度，這些麥類和奶製品吃多了，會讓孩子體內的濕氣越來越重。

身體一旦有濕氣，營養就很難吸收進去。嚴重一點，還會讓原本就敏感的體質變得更明顯——那長高這件事，自然就更難了。

🍚 你可以想像做麵包的麵團：水加太多，麵團就一直濕黏、成不了型。因為水氣全鎖在裡面，出不來。

孩子的身體也是一樣的道理。

📍 今晚就可以自己檢查兩件事：

第一，他的過敏、皮膚問題，這半年是不是越來越明顯？

第二，他上完廁所沖水後，馬桶上會不會黏著洗不掉的痕跡？

如果兩個都中——那真的該注意了。

👨‍⚕️ 我是馬丁醫師，台灣執照醫師，中西醫整合經驗超過 10 年，已陪伴 7000 多個華人家庭。

每個孩子的體質都不一樣，調理的方式也不會一樣。

📘 這個星期我有一堂免費線上分享會，我會教你用「中醫學 + 西方營養學」的方式：

📍 怎麼從孩子的舌頭狀況判斷他的體質
📍 哪些天天在吃的早餐，其實正在拖累他的吸收
📍 怎麼調理，才能幫他每年健康長高 6–8 公分

⏰ 免費，但名額有限，先到先得 👇 點擊下方連結，立即報名。

別讓一頓「很健康」的早餐，變成孩子長不高的原因。"""

CAP_V1 = """😴 你的孩子長不高，很可能不是因為吃得不夠——而是他的身體，已經累到吸收不了營養了。

你看看他一天是怎麼過的：

白天上學，放學後補習、學琴、打球，回到家吃完晚餐還要做 homework。

功課終於做完了，他又拿起手機、iPad，看一下 YouTube、玩一下遊戲。

⏰ 不知不覺，每天都拖到十一點多才睡。

👉 這樣下去，長高只會離他越來越遠。

很多家長會跟我說：「我的孩子有打籃球啊」「他每個星期都游泳」「他運動量已經很多了」。

但孩子的成長，從來不是有運動就夠了。

🛌 運動之後，還要有足夠的睡眠和恢復。如果白天行程排得滿滿，晚上又被 homework 和 screen time 拖到很晚——他真正能休息的時間，可能根本不夠。

所以看到孩子長得慢，請不要第一時間再幫他加一項運動、或再買一罐保健品。

📍 你真正該檢查的是這三件事：

他每天幾點睡？

睡前是不是還在看手機？

早上是不是經常很累、很難叫醒？

👨‍⚕️ 我是馬丁醫師，台灣執照醫師，中西醫整合經驗超過 10 年，已陪伴 7000 多個華人家庭。

📘 如果你的孩子今年 5 到 15 歲，homework、screen time 和課外活動都排得很滿、經常很晚才睡——歡迎你報名我的免費線上兒童長高分享會。

我會帶你從孩子的飲食、睡眠、運動和身體狀態開始檢查，找出現在最該優先調整的地方。

⏰ 名額有限 👇 點擊下方連結，立即免費報名。

不要一直往上加新方法。先把他每天的成長環境調好，才能真正幫到他。"""

CAP_V2 = """⚠️ 每年都帶孩子做 check-up，醫生每次都說：「他的身高還在正常範圍內。」

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

CAP_V5 = """⏳ 從現在，到你孩子的生長板閉合——你猜，還剩幾年？

很多爸媽以為還早。其實可能只剩兩三年，是他真正還能長高的時間。

🗣️「順其自然啦，等他大一點自己會抽高。」

這句話，我聽了十年。

😔 結果呢？很多家長是等到孩子十五、十六歲，突然不長了，才開始慌。那時候才來找我——說真的，剩下的時間已經不多了。

👉 你要知道，長高從來不是一條平平的直線。

它有一個黃金期。青春期一啟動，倒數計時就開始跑了。等那一波抽高結束、生長板閉合，身高就定型了。

這是骨頭的事，不是努力就能重來的事。

真正能讓你幫孩子追高的，就是中間那短短幾年。

👨‍⚕️ 我是馬丁醫師，台灣兒童長高專家，10 年中西醫整合經驗，已陪伴超過 7000 個華人家庭。

💔 這些年最讓我心疼的，永遠是同一種情況——孩子明明還有空間，卻因為爸媽一句「再等等看」，白白錯過。

反過來，願意早一點看清楚狀況的家庭，追回來的機會大得多。

📘 所以我把「怎麼判斷孩子還剩多少時間、這段時間到底該做什麼」，整理成一堂免費線上課《兒童長高方程式》：

📍 你的孩子還剩多少長高窗口期
📍 黃金期裡什麼該做、什麼絕對不能做
📍 怎麼在窗口關上前，幫他抓住每一公分

⏰ 名額有限 👇 點擊下方連結，立即免費報名。

別再用一句「順其自然」，賭掉孩子最後這幾年。"""


VIDEOS = [
    {"key": "SV1", "drive_id": "1coYtP68fjzLkImoJPWA9_DA1mJ_E9Cfa",
     "ad_name": "SV1：早餐就給錯了",
     "adset_name": "FR · SV1 早餐濕氣",
     "headline": "🔴 早餐這樣吃，孩子只會越吃越長不高",
     "caption": CAP_SV1},
    {"key": "V1", "drive_id": "1X2qPTXyhRzx-l4FEVIXSglap5hAl-_4w",
     "ad_name": "Video 1：身體很累了，你知道嗎？",
     "adset_name": "FR · V1 身體太累",
     "headline": "🔴 他不是不夠努力，是身體已經太累了",
     "caption": CAP_V1},
    {"key": "V2", "drive_id": "10QJAP56ClEeQhPWPYFONffPnPA9uVJ-V",
     "ad_name": "Video 2：每年帶孩子去 check-up",
     "adset_name": "FR · V2 check-up",
     "headline": "🔴 醫生說「正常範圍」，不代表他長得夠快",
     "caption": CAP_V2},
    {"key": "V5", "drive_id": "1hKjaZh-U-1vPOmoYSD6oXzZqrtLQ9vGw",
     "ad_name": "Video 5：倒數計時",
     "adset_name": "FR · V5 倒數計時",
     "headline": "🔴 生長板一閉合，再多錢也追不回來",
     "caption": CAP_V5},
]


def main() -> None:
    log = get_logger()
    s = load_settings()
    g = graph_client(s)
    drive = drive_client(s)

    st = state.load(STATE_KEY) or {}
    campaign_id = st.get("campaign_id")
    videos = dict(st.get("videos", {}))
    adsets = dict(st.get("adsets", {}))
    ads = dict(st.get("ads", {}))

    def persist():
        state.save(STATE_KEY, {"campaign_id": campaign_id, "videos": videos,
                               "adsets": adsets, "ads": ads})

    if not campaign_id:
        campaign_id = g.create_campaign(
            US_ACCT, name=CAMPAIGN_NAME, objective="OUTCOME_SALES", buying_type="AUCTION",
            status=STATUS, special_ad_categories=[],
            # ABO: required by Meta when there is no campaign budget. False keeps each ad set's
            # RM50 strictly its own, so the creative test stays clean.
            is_adset_budget_sharing_enabled=False)["id"]
        persist()
        log.info("created campaign %s (ABO)", campaign_id)

    dl = Path("/tmp/ca_1_4_1")
    dl.mkdir(parents=True, exist_ok=True)
    summary = []
    for v in VIDEOS:
        k = v["key"]
        if k not in videos:
            path = dl / f"{k}.mp4"
            drive.download_file(v["drive_id"], path)
            log.info("[%s] downloaded %d bytes", k, path.stat().st_size)
            videos[k] = g.upload_video(US_ACCT, str(path), v["ad_name"])
            persist()
            log.info("[%s] uploaded video -> %s", k, videos[k])

        if k not in adsets:
            adsets[k] = g.create_adset(
                US_ACCT, campaign_id=campaign_id, name=v["adset_name"],
                daily_budget=DAILY_CENTS, bid_strategy="LOWEST_COST_WITHOUT_CAP",
                optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                promoted_object={"pixel_id": PIXEL_ID,
                                 "custom_event_type": "COMPLETE_REGISTRATION"},
                targeting=TARGETING, status=STATUS)["id"]
            persist()
            log.info("[%s] created ad set %s", k, adsets[k])

        if k not in ads:
            video_data = {"video_id": videos[k], "title": v["headline"], "message": v["caption"],
                          "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
            thumb = g.get_video_thumbnail(videos[k])
            if thumb:
                video_data["image_url"] = thumb
            creative = g.create_adcreative(
                US_ACCT, name=v["ad_name"],
                object_story_spec={"page_id": PAGE_ID, "video_data": video_data},
                url_tags=UTM)
            ads[k] = g.create_ad(US_ACCT, name=v["ad_name"], adset_id=adsets[k],
                                 creative={"creative_id": creative["id"]}, status=STATUS)["id"]
            persist()
            summary.append(f"  {k:4} adset {adsets[k]} -> ad {ads[k]}")
            log.info("[%s] created ad %s", k, ads[k])

    log.info("=" * 60)
    for line in summary:
        log.info(line)
    final_summary(log, f"CA 1-4-1 ABO built ({STATUS}, RM50/day x 4 ad sets = RM200/day): "
                       f"campaign {campaign_id}, {len(ads)} ads.")


if __name__ == "__main__":
    main()
