"""One-off: build a 1-1-2 campaign (CBO RM100/day) on the cloned Parents-interest audience.

Operator request: new 1-1-2, RM100/day CBO, ad set = "Parents 兴趣定向" cloned from the
proven Advantage+ Parents + Engaged audience (real interest/behavior/family_status IDs read
live from ad set 120247164684970259 — never guessed). Videos:
  V11 = Martin May Video 11 (孩子快發育了，你還剩多少時間？)
  V13 = SGMY May Video 13 (一年比一年長得少)
  V14 = SGMY 14 (身高停在小學) — added later, turns the ad set into 1-1-3
Downloads each Drive video, uploads into the US account, builds campaign + ad set + ads
with the operator-approved (skill-written) captions + headlines + UTM url_tags, ACTIVE.
Idempotent via state — re-running only builds newly-added videos.
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
STATE_KEY = "entities_parents_interest_1_1_2"
DAILY_CENTS = 10000  # RM100.00/day CBO
STATUS = "ACTIVE"

CAMPAIGN_NAME = "PNW | Parents 兴趣定向 (clone A+P+E) | 1-1-2"
ADSET_NAME = "Parents 兴趣定向 (clone Advantage+ Parents + Engaged)"

# Cloned EXACTLY from live ad set 120247164684970259 (Parents 3-17 + Engaged) — real Meta IDs.
TARGETING = {
    "age_min": 25,
    "age_max": 65,
    "geo_locations": {
        "regions": [{"key": "3847"}, {"key": "3871"}, {"key": "3880"}, {"key": "3890"}],
        "location_types": ["home", "recent"],
    },
    "flexible_spec": [{
        "interests": [{"id": 6003263791114}, {"id": 6003346592981}],       # Shopping, Online shopping
        "behaviors": [{"id": 6071631541183}],                              # Engaged Shoppers
        "family_statuses": [{"id": 6023005529383}, {"id": 6023005570783},  # Parents 3-5, 6-8
                            {"id": 6023005681983}, {"id": 6023080302983}], # Parents 13-17, 9-12
    }],
    "excluded_custom_audiences": [
        {"id": "120236056842490259"},   # US 15days complete registration
        {"id": "120240867576290259"},   # MARTIN US PAID CUSTOMER - APR 13
        {"id": "120243775674560259"},   # US PAID STUDENTS MAY 2026
    ],
    "locales": [20, 21, 22],
    "targeting_automation": {"advantage_audience": 1},
}

V11_CAPTION = """⚠️ 你的女兒來 MC 了、兒子開始變聲了，卻還是長不高？如果被我說中——接下來這段你一定要看完。

很多華裔家長，是在孩子「開始發育」之後才緊張的。👀 女兒來月經、兒子長喉結變聲，才驚覺 😱 孩子好像沒怎麼長高。於是慌了——狂搜、問人、買保健品、催運動 🍼📉 結果還是沒動靜。

👉 但一個重要事實：女孩 MC 後平均還能長 3–5 年，男孩變聲後也還有補救期。只是 ⏳ 這補救期需要家長「主動管理」，不是順其自然就會長。不管理，就真的不再長，白白浪費最後機會。💔

我調查了 800 多位家長，很多孩子已 12–14 歲，保健品、湯方、跳繩、早睡全試過還沒效。為什麼？發育期內分泌在快速變化 🔄——你需要的不是重複無效的事，而是 ✅ 配合體質與發育節奏，在對的階段做對的事。尤其在北美，🍔 加工食品、🥤 冰飲、作息紊亂都在加速發育，你不介入，補救期只會越來越短。

👨‍⚕️ 我是馬丁藥師（台灣執照藥師 · 中西醫結合背景），幫助過無數已發育的孩子，橫跨台灣·馬來西亞·新加坡·香港·美國·加拿大，超過上千個家庭。很多家長帶著「來不及了」的絕望來找我——但方法對、時間點抓對，發育期反而是最後一次爆發長高的機會。

📘 這星期我開一堂免費線上課《兒童長高方程式》：
📍 你的孩子到底還剩多少長高窗口期
📍 發育期什麼該做、什麼絕對不能做
📍 怎麼在最後的窗口，幫孩子抓住每一公分

⏰ 名額有限 👇 點擊下方連結，立即免費報名。
現在不行動，這個窗口關了，就真的關了。"""

V13_CAPTION = """📉 三年前他長了 10 公分，去年剩 2 公分，今年——0。如果你孩子也「一年比一年長得少」，這段你必須看完。

判斷標準：👦 男孩 15 歲還不到 165cm、👧 女孩 15 歲還不到 155cm，代表生長速度已明顯放慢、甚至快停了。因為 15 歲已是青春期後半段、最後補救期 ⏳。網上都說「男 18 歲、女 MC 後兩年就停」，心涼一半——

👉 但一個很多人不知道的事實：生長板閉合不是「到某年齡一刀切」，而是漸進過程。有些孩子 16 歲還有空間，有些 14 歲就幾乎閉合。差別在體質——而體質，是可以調理的。

很多孩子閉合得快，不是年齡到了，而是體質長期「虛火」：🥤 冰飲奶製品過量、😴 睡眠不足、😣 壓力太大，這些會催熟身體、讓骨骼提前成熟。糾正過來、讓身體回到正常節奏，閉合有機會減慢，剩下空間才能好好利用。⛔ 但前提是不能再浪費時間——每過一天空間就少一點。15 歲看到還有兩三年，17 歲可能只剩幾個月。不管幾歲，今天都是你最早能行動的一天。

👨‍⚕️ 我是馬丁藥師，兒童自然長高研究超過十年——不打針、不賣藥、不用生長激素，只用一套從體質根源出發的調理方法。橫跨六國、上千個家庭，很多帶著絕望來的家長，最後都帶著驚喜離開。

📘 這星期我開一堂免費線上課《兒童長高方程式》：
📍 你的孩子到底還剩多少長高窗口期
📍 發育期什麼該做、什麼絕對不能做
📍 怎麼在最後的窗口，幫孩子抓住每一公分

⏰ 名額有限 👇 點擊下方連結，立即免費報名。
現在不行動，這個窗口關了，就真的關了。"""

V14_CAPTION = """⚠️ 如果你的孩子已經上中學了，身高卻還停在小學的水平——你真的要注意了。

我見過太多這種案例：👀 小學畢業時 140 幾公分，想著「還好，等青春期再長」。結果上了中學一年、兩年、三年，身高幾乎沒動 📉。同學一個個在飆高，你的孩子站在旁邊，還是小學時的樣子。你有沒有想過，為什麼？

🗣️ 很多家長以為：青春期一到，孩子自然會長高。
👉 但事實是——青春期是長高的「機會」，不是「保證」。孩子進入青春期了，身體如果不具備長高的條件，機會來了也抓不住。

什麼叫「條件」？三個關鍵：
🥣 脾胃功能正常——吃進去的營養，身體能真正吸收利用
😴 睡眠品質好——深度睡眠時，生長激素才會大量分泌
🌿 體質沒有失衡——在北美，孩子長期冰飲、加工飲食，體質容易偏濕偏熱，直接拖慢骨骼生長速度

這三個條件，缺任何一個，青春期的長高機會就被白白浪費了。💔

👨‍⚕️ 我是馬丁藥師（台灣執照藥師 · 中西醫結合背景），十多年來幫助過無數孩子，橫跨台灣·馬來西亞·新加坡·香港·美國·加拿大，超過上千個家庭。很多家長帶著「來不及了」的絕望來找我——但只要方法對、時間點抓對，青春期反而是最後一次爆發長高的機會。

📘 這星期我開一堂免費線上課《兒童長高方程式》：
📍 你的孩子到底還剩多少長高窗口期
📍 發育期什麼該做、什麼絕對不能做
📍 怎麼在最後的窗口，幫孩子抓住每一公分

⏰ 名額有限 👇 點擊下方連結，立即免費報名。
現在不行動，這個窗口關了，就真的關了。"""

VIDEOS = [
    {"key": "V11", "drive_id": "17EC5vCjPQBbs7tPIbPg8RKfXsGUkbnZx",
     "ad_name": "Video 11：孩子快發育了，你還剩多少時間？",
     "headline": "🔴 孩子開始發育了，你還剩多少長高時間？",
     "caption": V11_CAPTION},
    {"key": "V13", "drive_id": "1VCbh8D55mDlMz78D1l9CQvusAp1gLNCC",
     "ad_name": "Video 13：一年比一年長得少",
     "headline": "🔴 一年比一年長得少？生長板正在悄悄關上",
     "caption": V13_CAPTION},
    {"key": "V14", "drive_id": "16FJbD3oCzmKLCosjRZ760r8qOpq_2Xzu",
     "ad_name": "Video 14：身高停在小學",
     "headline": "🔴 上了中學，身高卻還停在小學？",
     "caption": V14_CAPTION},
]


def main() -> None:
    log = get_logger()
    s = load_settings()
    g = graph_client(s)
    drive = drive_client(s)

    st = state.load(STATE_KEY) or {}
    campaign_id = st.get("campaign_id")
    adset_id = st.get("adset_id")
    videos = dict(st.get("videos", {}))   # key -> video_id
    ads = dict(st.get("ads", {}))         # key -> ad_id

    def persist():
        state.save(STATE_KEY, {"campaign_id": campaign_id, "adset_id": adset_id,
                               "videos": videos, "ads": ads})

    # 1) campaign (CBO RM100/day)
    if not campaign_id:
        campaign_id = g.create_campaign(
            US_ACCT, name=CAMPAIGN_NAME, objective="OUTCOME_SALES", buying_type="AUCTION",
            status=STATUS, special_ad_categories=[], daily_budget=DAILY_CENTS,
            bid_strategy="LOWEST_COST_WITHOUT_CAP")["id"]
        persist()
        log.info("created campaign %s", campaign_id)

    # 2) ad set (cloned Parents-interest targeting)
    if not adset_id:
        adset_id = g.create_adset(
            US_ACCT, campaign_id=campaign_id, name=ADSET_NAME,
            optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
            promoted_object={"pixel_id": PIXEL_ID, "custom_event_type": "COMPLETE_REGISTRATION"},
            targeting=TARGETING, status=STATUS)["id"]
        persist()
        log.info("created ad set %s", adset_id)

    # 3) upload videos + build one ad each
    dl = Path("/tmp/parents_interest")
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
    final_summary(log, f"Parents-interest build ({STATUS}, CBO RM100/day): "
                       f"campaign {campaign_id}, adset {adset_id}, {len(ads)} ads.")


if __name__ == "__main__":
    main()
