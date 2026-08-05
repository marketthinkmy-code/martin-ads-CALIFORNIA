"""One-off: build TWO 1-1-3 campaigns (CBO RM100/day) with the same 3 videos.

Operator request: same 3 creatives (V5 過敏篇 / V6 15歲以上試五六種 / V7 孩子來MC了) on two
audiences —
  FR = interest: Family & Relationships (real interest IDs cloned from live adset 120247153008970259)
  PE = Parents 3-17 + Engaged (cloned from live adset 120247164684970259)
Uploads each Drive video ONCE (video_id is account-scoped, reused across both campaigns), then
builds 2 campaigns × (1 adset + 3 ads) with skill-written captions (馬丁醫師) + 🔴 headlines +
UTM url_tags, ACTIVE. Idempotent via state.
"""
from __future__ import annotations

from pathlib import Path

from adbot import state
from adbot.commands import drive_client, graph_client
from adbot.logging import final_summary, get_logger
from adbot.settings import load_settings

US_ACCT = "act_1629566827721449"
PAGE_ID = "1180683238455992"
PIXEL_ID = "1921735088376759"
LINK = "https://kidsgrowthformula.com/webinar-main-page"
UTM = "utm_source={{adset.name}}&utm_medium={{placement}}&utm_campaign={{campaign.name}}&utm_content={{ad.name}}"
STATE_KEY = "entities_two_1_1_3_fr_pe"
DAILY_CENTS = 10000  # RM100.00/day CBO each
STATUS = "ACTIVE"

GEO = {"regions": [{"key": "3847"}, {"key": "3871"}, {"key": "3880"}, {"key": "3890"}],
       "location_types": ["home", "recent"]}
EXCLUDE = [{"id": "120236056842490259"}, {"id": "120240867576290259"}, {"id": "120243775674560259"}]

# interest: Family & Relationships — real IDs cloned from live adset 120247153008970259
TARGETING_FR = {
    "age_min": 25, "age_max": 65, "geo_locations": GEO, "locales": [20, 21, 22],
    "flexible_spec": [{"interests": [
        {"id": 6002991239659},  # Motherhood
        {"id": 6003101323797},  # Fatherhood
        {"id": 6003232518610},  # Parenting
        {"id": 6003409392877},  # Weddings
        {"id": 6003445506042},  # Marriage
        {"id": 6003476182657},  # Family
        {"id": 6004100985609},  # Friendship
    ]}],
    "excluded_custom_audiences": EXCLUDE,
    "targeting_automation": {"advantage_audience": 1},
}

# Parents 3-17 + Engaged — real IDs cloned from live adset 120247164684970259
TARGETING_PE = {
    "age_min": 25, "age_max": 65, "geo_locations": GEO, "locales": [20, 21, 22],
    "flexible_spec": [{
        "interests": [{"id": 6003263791114}, {"id": 6003346592981}],
        "behaviors": [{"id": 6071631541183}],
        "family_statuses": [{"id": 6023005529383}, {"id": 6023005570783},
                            {"id": 6023005681983}, {"id": 6023080302983}],
    }],
    "excluded_custom_audiences": EXCLUDE,
    "targeting_automation": {"advantage_audience": 1},
}

AUDIENCES = [
    {"key": "FR", "targeting": TARGETING_FR,
     "campaign_name": "PNW | Family & Relationships | 1-1-3 (V5/6/7)",
     "adset_name": "interest: Family & Relationships"},
    {"key": "PE", "targeting": TARGETING_PE,
     "campaign_name": "PNW | Parents 3-17 + Engaged | 1-1-3 (V5/6/7)",
     "adset_name": "Parents 3-17 + Engaged"},
]

V5_CAPTION = """😴 你的孩子是不是常常鼻塞、打噴嚏、皮膚癢、晚上睡不好？
你以為這只是過敏——但我告訴你，這很可能正是他長不高的原因。

很多住在美國、加拿大的華人家長都遇過：孩子鼻敏感、皮膚敏感、食物敏感，晚上不是鼻塞就是皮膚癢，睡到一半還會醒。
你可能已經看過醫生、吃過過敏藥、抹過藥膏，症狀有改善——
但你有沒有發現？😔 睡眠還是不穩、胃口還是不好、白天容易累容易煩、身高也沒明顯追上同齡孩子。

👉 很多家長從沒把「過敏、睡眠、長高」放在一起看，但這三件事是連在一起的。
孩子要長得好，深度睡眠非常重要——那是身體修復、成長的關鍵時間。如果晚上鼻塞、呼吸不順、皮膚癢到半夜醒，他就很難進入穩定的深層睡眠。

所以問題不只是「過敏有沒有控制住」，你還要看：🛌 孩子睡得深不深、醒來有沒有精神、🍚 胃口好不好、過去半年一年身高到底長了多少。
在北美，🧀 cheese、pizza、sandwich、ice cream、甜食冷飲變得很常見，對某些孩子長期這樣吃，身體負擔越來越重——你看到的是鼻敏感、皮膚癢、睡不好，背後可能還有胃口差、消化弱、體質失衡。藥物能控制症狀，但如果睡眠沒變深、成長速度沒回來，身高就可能一直卡住。

👨‍⚕️ 我是馬丁醫師，來自台灣，研究兒童自然成長超過十年，幫助過台灣·香港·馬來西亞·新加坡·美國·加拿大的華人家庭。我用中西結合的判斷方法：西醫看成長速度、睡眠、營養、發育階段；中醫看體質、脾胃、過敏、身體負擔——幫父母完整判斷孩子是單純過敏，還是身體狀態已經影響成長。

📘 這星期免費線上課《兒童長高方程式》，我會教你：
📍 為什麼過敏和睡眠會影響成長速度
📍 北美華人孩子常見的飲食、作息、體質問題
📍 怎麼判斷孩子是正常慢發育，還是身體已經卡住
📍 怎麼從飲食、睡眠、運動、體質調整，幫孩子回到更好的成長狀態

孩子 7–15 歲、尤其有過敏／睡不好／胃口差、又長得比同齡慢——
⏰ 名額有限 👇 點擊下方連結，立即免費報名。
別只把過敏當小問題——先看清楚它有沒有正在偷走孩子的睡眠和身高。"""

V6_CAPTION = """孩子已經 15 歲以上，補品吃了、牛奶喝了、運動也做了，身高還是卡住？
那問題可能不是你做得不夠，而是方向一開始就錯了。⚠️

我最近看了 58 位住在美國、加拿大的華人家長回饋，發現一個很常見的情況：很多孩子 15 歲以上，半年沒怎麼長、一年沒怎麼長，有些甚至兩年幾乎沒動。
家長不是沒努力——🍼 calcium gummies、蛋白粉、增高奶粉、看專科、照骨齡、跳繩、打籃球、早睡……很多方法都試過，有些甚至花了幾千美金，孩子身高還是沒明顯變化。
於是更焦慮：「是不是太遲了？」「是不是骨齡快閉合了？」「是不是基因真的沒辦法？」

👉 但問題不一定是你試得不夠多，而是——你一直在往孩子身上「加東西」：加保健品、加牛奶、加運動、加補品，卻很少有人停下來問：孩子到底為什麼長不動？
有些孩子是 😴 睡眠品質不好、有些是 🍚 胃口差消化弱、有些是 🤧 過敏反覆晚上睡不深、有些是 🏃 運動方式不適合現在的發育階段。
真正重要的不是繼續亂試，而是先判斷：孩子現在還有沒有成長空間？成長速度是不是已經慢下來？身體到底卡在睡眠、營養、還是體質？沒搞清楚，買再多 supplement 也可能只是原地踏步。

👨‍⚕️ 我是馬丁醫師。我做的第一件事，不是叫家長再買更多東西，而是用中西結合的方式先幫父母看懂孩子卡在哪裡：西醫看成長速度、營養、睡眠、發育階段、骨骼狀態；中醫看體質、脾胃、過敏、身體負擔。

📘 這星期免費線上課《兒童長高方程式》，我會教你判斷：
📍 孩子現在到底還有沒有成長空間
📍 為什麼補品、牛奶、運動都做了身高還是卡住
📍 青春期孩子該怎麼調整飲食、睡眠、運動與體質
📍 什麼情況下不能再只是繼續等

孩子 10–17 歲、尤其 13 歲以上、過去一年長得很慢——
⏰ 名額有限 👇 點擊下方連結，立即免費報名。
不要再靠猜——先搞清楚孩子現在到底卡在哪裡。"""

V7_CAPTION = """你的女兒來 MC 了、兒子開始變聲了，卻還是長不高？！
如果被我說中，接下來這段你一定要看完。

很多家長都是在孩子「開始發育」之後才突然緊張——女兒來月經、兒子長喉結聲音變粗，才發現孩子好像還沒長到理想身高。😱 然後開始慌：上網查、到處問、買 supplement、買蛋白粉、催跳繩打籃球早睡。做了一堆，身高還是沒什麼動。這時候父母真正害怕的不是矮，而是怕自己已經太遲發現。

👉 一個很重要的事實：女孩來 MC 後平均還能長 3–5 年，男孩變聲後也還有補救期。但這個補救期需要家長「及時管理」——不是順其自然就會長；到了補救期還不管理，就真的不會再長，白白浪費最後的機會。
我調查了 58 位住在美國、加拿大的華人家長，很多孩子已 12、13、14 歲，過去幾年 supplement、蛋白粉、看專科、跳繩、早睡什麼都試了還是沒效，現在進入青春期，真的慌了。
問題是：發育期不是做越多越好，而是先判斷孩子卡在哪裡，再配合體質、睡眠、飲食、運動與發育節奏，在對的時間做對的調整。尤其在北美長大的華人孩子，飲食、作息、課業壓力、after-school 活動都可能影響成長節奏——父母不能只靠猜。

👨‍⚕️ 我是馬丁醫師，十多年來幫助過無數已開始發育的孩子，橫跨台灣·馬來西亞·新加坡·香港·美國·加拿大，上千個家庭。我用中西結合的判斷方式：西醫看成長速度、營養、睡眠、發育階段、骨骼狀態；中醫看體質、脾胃、過敏、身體負擔——幫父母完整判斷孩子還有沒有成長空間、現在最該調整什麼。

📘 這星期免費線上課《兒童長高方程式》，我會教你：
📍 你的孩子到底還剩多少長高窗口期
📍 發育期什麼該做、什麼絕對不能做
📍 怎麼在最後的窗口，幫孩子抓住每一公分

孩子 10–17 歲、尤其已進入青春期、過去一年長得很慢——
⏰ 名額有限 👇 點擊下方連結，立即免費報名。
別等窗口關了才後悔——現在就先搞清楚孩子卡在哪裡。"""

VIDEOS = [
    {"key": "V5", "drive_id": "1ysClbsrtSx1D57PeF-FscSYw-KwPe9jq",
     "ad_name": "Video 5：過敏篇", "headline": "🔴 孩子過敏、睡不好？這可能正是他長不高的原因",
     "caption": V5_CAPTION},
    {"key": "V6", "drive_id": "1XeeMzJXo4BkFlvb2-07hRUbO4_iz2zKL",
     "ad_name": "Video 6：15 歲以上試了五六種方法", "headline": "🔴 15 歲以上、五六種方法都試過，身高還是卡住？",
     "caption": V6_CAPTION},
    {"key": "V7", "drive_id": "1vjvihAMLqYhG0ElmjzP2qSwSkp_lGCOY",
     "ad_name": "Video 7：孩子來MC了 / 你還剩多少時間？", "headline": "🔴 孩子快發育了，你還剩多少長高時間？",
     "caption": V7_CAPTION},
]


def main() -> None:
    log = get_logger()
    s = load_settings()
    g = graph_client(s)
    drive = drive_client(s)

    st = state.load(STATE_KEY) or {}
    videos = dict(st.get("videos", {}))       # vkey -> video_id
    auds = dict(st.get("audiences", {}))      # akey -> {campaign_id, adset_id}
    ads = dict(st.get("ads", {}))             # "akey:vkey" -> ad_id

    def persist():
        state.save(STATE_KEY, {"videos": videos, "audiences": auds, "ads": ads})

    # 1) upload each video ONCE
    dl = Path("/tmp/two_1_1_3")
    dl.mkdir(parents=True, exist_ok=True)
    for v in VIDEOS:
        if v["key"] not in videos:
            path = dl / f"{v['key']}.mp4"
            drive.download_file(v["drive_id"], path)
            videos[v["key"]] = g.upload_video(US_ACCT, str(path), v["ad_name"])
            persist()
            log.info("uploaded %s -> %s", v["key"], videos[v["key"]])

    # 2) per audience: campaign + adset + 3 ads
    summary = []
    for aud in AUDIENCES:
        ak = aud["key"]
        rec = dict(auds.get(ak, {}))
        if not rec.get("campaign_id"):
            rec["campaign_id"] = g.create_campaign(
                US_ACCT, name=aud["campaign_name"], objective="OUTCOME_SALES", buying_type="AUCTION",
                status=STATUS, special_ad_categories=[], daily_budget=DAILY_CENTS,
                bid_strategy="LOWEST_COST_WITHOUT_CAP")["id"]
            auds[ak] = rec
            persist()
            log.info("[%s] created campaign %s", ak, rec["campaign_id"])
        if not rec.get("adset_id"):
            rec["adset_id"] = g.create_adset(
                US_ACCT, campaign_id=rec["campaign_id"], name=aud["adset_name"],
                optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                promoted_object={"pixel_id": PIXEL_ID, "custom_event_type": "COMPLETE_REGISTRATION"},
                targeting=aud["targeting"], status=STATUS)["id"]
            auds[ak] = rec
            persist()
            log.info("[%s] created ad set %s", ak, rec["adset_id"])
        for v in VIDEOS:
            adkey = f"{ak}:{v['key']}"
            if adkey in ads:
                continue
            vid = videos[v["key"]]
            thumb = g.get_video_thumbnail(vid)
            video_data = {"video_id": vid, "title": v["headline"], "message": v["caption"],
                          "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
            if thumb:
                video_data["image_url"] = thumb
            creative = g.create_adcreative(
                US_ACCT, object_story_spec={"page_id": PAGE_ID, "video_data": video_data},
                url_tags=UTM)
            ad = g.create_ad(US_ACCT, name=v["ad_name"], adset_id=rec["adset_id"],
                             creative={"creative_id": creative["id"]}, status=STATUS)
            ads[adkey] = ad["id"]
            persist()
            summary.append(f"  {adkey} -> ad {ad['id']}")
            log.info("[%s] built %s -> ad %s", ak, v["key"], ad["id"])

    log.info("=" * 60)
    for line in summary:
        log.info(line)
    final_summary(log, f"Two 1-1-3 built ({STATUS}, CBO RM100/day each): "
                       f"FR campaign {auds.get('FR', {}).get('campaign_id')}, "
                       f"PE campaign {auds.get('PE', {}).get('campaign_id')}, {len(ads)} ads total.")


if __name__ == "__main__":
    main()
