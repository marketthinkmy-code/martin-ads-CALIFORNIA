"""One-off: build a single-IMAGE 1-1-3 campaign (CBO RM100/day) on Advantage+ Parents+Engaged.

Operator request: 3 single-image ads on the Advantage+ Parents + Engaged audience (real
interest/behavior/family_status IDs cloned from live ad set 120247164684970259, advantage
audience ON). Downloads each Drive PNG, uploads it into the US account (image_hash), builds
campaign + ad set + 3 single-image ads with the operator-supplied captions + 🔴 headlines +
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
STATE_KEY = "entities_single_image_1_1_3"
DAILY_CENTS = 10000  # RM100.00/day CBO
STATUS = "ACTIVE"

CAMPAIGN_NAME = "PNW | Single Image · Advantage+ Parents+Engaged | 1-1-3"
ADSET_NAME = "Advantage+ Parents + Engaged (single image)"

# Cloned from live ad set 120247164684970259 — real Meta IDs, advantage_audience ON.
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

IMG1_CAPTION = """跟著美國人吃肉、喝牛奶，孩子的體重升了，身高卻依然停滯不前。💔
身為台灣家長，你是否也感到無力：
❓是不是亞洲人的基因，本來就比較吃虧？
❓已經跟著美國人的食譜，怎麼還是長不高？
❓每天高強度運動，到底哪裡做錯了？
其實，長高不用靠運氣，更不需要盲目摸索！
只要把握 15 歲前的黃金發育期，
利用科學的飲食結構、睡眠優化與發育管理，
華人孩子一樣能突破限制，發揮最大的成長潛能！🌟
過去 2 年，馬丁藥師已透過科學方法，
陪伴全球 7000+ 個家庭 克服發育焦慮，
幫助無數海外華人孩子，在美式校園裡找回自信！
孩子的成長不能重來，別讓身高，限制了孩子未來的舞台。
📘《兒童長高方程式》免費線上講座
專為海外華人家庭設計，全面解密科學長高關鍵！"""

IMG2_CAPTION = """很多住在美國的台灣家長，
看著當地孩子突飛猛進，心裡一急，就容易陷入嚴重的養育盲點：
❌ 盲目補鈣過量
❌ 複製美式飲食
❌ 高強度體能爆發
馬丁藥師必須提醒大家：
華人孩子的體質與吸收機制，別再照搬美式的養育邏輯！
長高不是拚命餵食，更不是靠運氣摸索。
而是要在 3 到 15 歲的黃金窗口期，
進行精準的睡眠週期優化、骨骼營養吸收發揮，以及生長訊號的調控。
只要方向對了，即便父母身高不突出，孩子依然能衝破遺傳限制！
在這場線上講座中，馬丁藥師將用最扎實的科學數據，
帶您全面拆解海外華人兒童的成長密碼。
📘《兒童長高方程式》免費線上講座，立即報名。"""

IMG3_CAPTION = """明明天天照著美國人的方法養，孩子的身高到底卡在哪❓
在美國養孩子，台灣家長常掉入兩難陷阱：
❌ 照美式養法：牛奶起司天天塞，沒長高反而先長了一肚子肉！
❌ 照台灣偏方：跨海寄轉骨湯、草藥一直灌，孩子脾胃吸收不了反而拉肚子！
長高不是靠盲目堆熱量，更不是靠運氣！
華人孩子的骨骼吸收機制，跟美式飲食根本對不上。
用錯方法，只是在白白浪費孩子僅有的發育期！
明晚直播間，我們邀請兒童成長專家 —— 馬丁藥師，用醫學實證幫你打通養育迷思！
過去 2 年，全球已有 7000+ 個海外家庭，跟著這套科學方法，幫孩子重新拉高發育曲線。
💡 我們不賣焦慮，只講純實用科學：
🚫 不上昂貴生長針　🚫 不逼孩子吃苦藥　🚫 不做魔鬼高強度訓練
🔍 直播 2 小時，帶你釐清 3 大發育密碼：
1️⃣ 孩子是什麼體質？
2️⃣ 還有多少成長黃金時間？
3️⃣ 什麼方式更適合自己的孩子？
結合美式作息，訂製最適合你孩子的成長方案！
📘《兒童長高方程式》免費線上講座，立即報名。"""

IMAGES = [
    {"key": "IMG1", "drive_id": "1wdKkFyrt24Ed3gEPOs9ZIIe76YMkc5_J",
     "ad_name": "Single image 1：跟著美國人吃，孩子卻停滯",
     "headline": "🔴 跟著美國人吃，孩子為什麼還是長不高？",
     "caption": IMG1_CAPTION},
    {"key": "IMG2", "drive_id": "1wpyc6iDIPSdtRMuX-pd85P33YYKcpeQe",
     "ad_name": "Single image 2：別照搬美式養育邏輯",
     "headline": "🔴 華人孩子，別再照搬美式養育邏輯",
     "caption": IMG2_CAPTION},
    {"key": "IMG3", "drive_id": "16Ma5Dz18b8WLSWL0qQFf2LZoGN7gbfvH",
     "ad_name": "Single image 3：照美國方法養卻卡住",
     "headline": "🔴 天天照美國方法養，身高到底卡在哪？",
     "caption": IMG3_CAPTION},
]


def main() -> None:
    log = get_logger()
    s = load_settings()
    g = graph_client(s)
    drive = drive_client(s)

    st = state.load(STATE_KEY) or {}
    campaign_id = st.get("campaign_id")
    adset_id = st.get("adset_id")
    hashes = dict(st.get("hashes", {}))   # key -> image_hash
    ads = dict(st.get("ads", {}))         # key -> ad_id

    def persist():
        state.save(STATE_KEY, {"campaign_id": campaign_id, "adset_id": adset_id,
                               "hashes": hashes, "ads": ads})

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

    dl = Path("/tmp/single_image")
    dl.mkdir(parents=True, exist_ok=True)
    summary = []
    for im in IMAGES:
        if im["key"] not in hashes:
            path = dl / f"{im['key']}.png"
            drive.download_file(im["drive_id"], path)
            hashes[im["key"]] = g.upload_image(US_ACCT, str(path))
            persist()
            log.info("uploaded %s -> hash %s", im["key"], hashes[im["key"]])
        if im["key"] not in ads:
            link_data = {"link": LINK, "image_hash": hashes[im["key"]],
                         "message": im["caption"], "name": im["headline"],
                         "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
            creative = g.create_adcreative(
                US_ACCT, object_story_spec={"page_id": PAGE_ID, "link_data": link_data},
                url_tags=UTM)
            ad = g.create_ad(US_ACCT, name=im["ad_name"], adset_id=adset_id,
                             creative={"creative_id": creative["id"]}, status=STATUS)
            ads[im["key"]] = ad["id"]
            persist()
            summary.append(f"  {im['key']} -> ad {ad['id']}")
            log.info("built %s -> ad %s", im["key"], ad["id"])

    log.info("=" * 60)
    log.info("campaign %s / adset %s", campaign_id, adset_id)
    for line in summary:
        log.info(line)
    final_summary(log, f"Single-image 1-1-3 built ({STATUS}, CBO RM100/day): "
                       f"campaign {campaign_id}, adset {adset_id}, {len(ads)} ads.")


if __name__ == "__main__":
    main()
