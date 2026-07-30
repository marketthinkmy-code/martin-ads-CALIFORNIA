"""One-off: build a 1-1-2 campaign (CBO RM100/day) on the cloned Parents-interest audience.

Second Parents-interest 1-1-2 (operator request). Ad set cloned from the proven
Advantage+ Parents + Engaged audience (real IDs from live ad set 120247164684970259).
Videos:
  V7  = SGMY May Video 7  (15 歲還沒抽高，是不是已經太遲？)
  V16 = SGMY May Video 16 (身高永遠停在 15 歲)
Downloads each Drive video, uploads into the US account, builds campaign + ad set + 2 ads
with skill-written captions + 🔴 headlines + UTM url_tags, ACTIVE. Idempotent via state.
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
STATE_KEY = "entities_parents_interest_v7_v16"
DAILY_CENTS = 10000  # RM100.00/day CBO
STATUS = "ACTIVE"

CAMPAIGN_NAME = "PNW | Parents 兴趣定向 (clone A+P+E) #2 | 1-1-2"
ADSET_NAME = "Parents 兴趣定向 (clone Advantage+ Parents + Engaged) #2"

# Cloned EXACTLY from live ad set 120247164684970259 — real Meta IDs.
TARGETING = {
    "age_min": 25,
    "age_max": 65,
    "geo_locations": {
        "regions": [{"key": "3847"}, {"key": "3871"}, {"key": "3880"}, {"key": "3890"}],
        "location_types": ["home", "recent"],
    },
    "flexible_spec": [{
        "interests": [{"id": 6003263791114}, {"id": 6003346592981}],
        "behaviors": [{"id": 6071631541183}],
        "family_statuses": [{"id": 6023005529383}, {"id": 6023005570783},
                            {"id": 6023005681983}, {"id": 6023080302983}],
    }],
    "excluded_custom_audiences": [
        {"id": "120236056842490259"},
        {"id": "120240867576290259"},
        {"id": "120243775674560259"},
    ],
    "locales": [20, 21, 22],
    "targeting_automation": {"advantage_audience": 1},
}

V7_CAPTION = """😰 孩子 15 歲了，還沒明顯抽高——是不是已經太遲？
我直接告訴你：不一定。
但如果你還在用同一個方法「等他自己長」，那才是真的危險。⚠️
因為 15 歲之後，孩子已經不是單純靠自然成長就會一直長高的階段了。

🗣️「男生比較慢發育，遲一點就高了。」
🗣️「女生只是還沒發育完，之後會追上。」
這句話——只對一半。
男生確實有機會長到比較後期，女生初潮後也不是馬上停止成長。
👉 但重點是：孩子有沒有成長空間，不是靠猜的。要看他的發育階段、體質、吸收能力、睡眠與運動方式，還有骨骼成長狀態。

很多家長錯就錯在：孩子已經進入青春期後期，卻還在用小學階段的方法——繼續多喝奶、吃保健品、隨便運動，然後期待他突然抽高。
問題是，如果 🥣 吸收不好、😴 睡眠時間不對、🏃 運動方式不適合，你做再多，可能都只是白忙。

👨‍⚕️ 我是馬丁藥師。過去幫助過來自馬來西亞·新加坡·美國·加拿大·台灣·香港的孩子，發現一個共同點：不是每個孩子都沒機會，真正的問題是——很多家長太遲發現孩子卡在哪裡。

📘 這星期我開一場免費線上課《兒童長高方程式》，專門教家長判斷：
📍 孩子現在到底還有沒有成長空間
📍 為什麼吃了補品還是沒效果
📍 什麼運動適合、什麼反而不適合
📍 青春期孩子該怎麼調整飲食、作息與體質

孩子大概 5–17 歲、尤其已經開始擔心身高的階段——
⏰ 名額有限 👇 點擊下方連結，立即免費報名。
不要再靠猜——先搞清楚孩子現在到底卡在哪裡。"""

V16_CAPTION = """他不會永遠都是 15 歲。但他的身高，可能永遠停在 15 歲。

這句話聽起來很殘酷，但這就是現實。😔
你的孩子會長大、會畢業、會工作、會組建家庭——年齡會一直往前走。
但如果你在他 15 歲時沒做對的事，他 20 歲、30 歲、40 歲的身高，可能就永遠停在今天這個數字。
他會帶著這個身高去當兵、去面試、去社交、去相親——帶著它，活一輩子。💔

15 歲，是一個分水嶺。
在這之前，你可以慢慢來、可以試錯、可以等；但在這之後，每一天都在倒數。⏳
孩子的生長板正在逐漸閉合。閉合速度取決於兩件事：一是年齡，二是體質。年齡你改變不了，但體質你可以調理。
✅ 如果能在生長板完全閉合前，把 🥣 脾胃功能調好、😴 睡眠品質改善、🌿 體質失衡糾正，他的身體還有能力再長。
但如果繼續什麼都不做、或繼續用錯方法——等到生長板完全閉合那天，一切就都結束了。而那一天不會通知你，它就這樣靜靜地來了。

👨‍⚕️ 我是馬丁藥師（台灣執照藥師 · 中西醫結合背景），十多年來幫助過無數孩子，橫跨台灣·馬來西亞·新加坡·香港·美國·加拿大，上千個家庭。很多家長帶著「來不及了」的絕望來找我——但只要方法對、時間點抓對，青春期反而是最後一次爆發長高的機會。

📘 這星期免費線上課《兒童長高方程式》：
📍 你的孩子還剩多少長高窗口期
📍 發育期什麼該做、什麼絕對不能做
📍 怎麼在最後的窗口，幫孩子抓住每一公分

⏰ 名額有限，坐滿即止。👇 點擊下方連結，立即免費報名。
他的身高不該停在 15 歲——別讓「靜靜來的那一天」，替你做了決定。"""

VIDEOS = [
    {"key": "V7", "drive_id": "1zpCkfT3BNxbJrJ-SbXm1GsURzsFI4nvx",
     "ad_name": "Video 7：15 歲還沒抽高，是不是已經太遲？",
     "headline": "🔴 15 歲還沒抽高，是不是已經太遲？",
     "caption": V7_CAPTION},
    {"key": "V16", "drive_id": "1U3m03mYstMMRQ4yRdJ-QzbxgV7mXj4UA",
     "ad_name": "Video 16：身高永遠停在 15 歲",
     "headline": "🔴 他不會永遠 15 歲，但身高可能永遠停在 15 歲",
     "caption": V16_CAPTION},
]


def main() -> None:
    log = get_logger()
    s = load_settings()
    g = graph_client(s)
    drive = drive_client(s)

    st = state.load(STATE_KEY) or {}
    campaign_id = st.get("campaign_id")
    adset_id = st.get("adset_id")
    videos = dict(st.get("videos", {}))
    ads = dict(st.get("ads", {}))

    def persist():
        state.save(STATE_KEY, {"campaign_id": campaign_id, "adset_id": adset_id,
                               "videos": videos, "ads": ads})

    if not campaign_id:
        campaign_id = g.create_campaign(
            US_ACCT, name=CAMPAIGN_NAME, objective="OUTCOME_SALES", buying_type="AUCTION",
            status=STATUS, special_ad_categories=[], daily_budget=DAILY_CENTS,
            bid_strategy="LOWEST_COST_WITHOUT_CAP")["id"]
        persist()
        log.info("created campaign %s", campaign_id)

    if not adset_id:
        adset_id = g.create_adset(
            US_ACCT, campaign_id=campaign_id, name=ADSET_NAME,
            optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
            promoted_object={"pixel_id": PIXEL_ID, "custom_event_type": "COMPLETE_REGISTRATION"},
            targeting=TARGETING, status=STATUS)["id"]
        persist()
        log.info("created ad set %s", adset_id)

    dl = Path("/tmp/parents_interest_v7v16")
    dl.mkdir(parents=True, exist_ok=True)
    summary = []
    for v in VIDEOS:
        if v["key"] not in videos:
            path = dl / f"{v['key']}.mp4"
            drive.download_file(v["drive_id"], path)
            videos[v["key"]] = g.upload_video(US_ACCT, str(path), v["ad_name"])
            persist()
            log.info("uploaded %s -> %s", v["key"], videos[v["key"]])
        if v["key"] not in ads:
            vid = videos[v["key"]]
            thumb = g.get_video_thumbnail(vid)
            video_data = {"video_id": vid, "title": v["headline"], "message": v["caption"],
                          "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
            if thumb:
                video_data["image_url"] = thumb
            creative = g.create_adcreative(
                US_ACCT, object_story_spec={"page_id": PAGE_ID, "video_data": video_data},
                url_tags=UTM)
            ad = g.create_ad(US_ACCT, name=v["ad_name"], adset_id=adset_id,
                             creative={"creative_id": creative["id"]}, status=STATUS)
            ads[v["key"]] = ad["id"]
            persist()
            summary.append(f"  {v['key']} -> ad {ad['id']}")
            log.info("built %s -> ad %s", v["key"], ad["id"])

    log.info("=" * 60)
    log.info("campaign %s / adset %s", campaign_id, adset_id)
    for line in summary:
        log.info(line)
    final_summary(log, f"Parents-interest #2 1-1-2 built ({STATUS}, CBO RM100/day): "
                       f"campaign {campaign_id}, adset {adset_id}, {len(ads)} ads.")


if __name__ == "__main__":
    main()
