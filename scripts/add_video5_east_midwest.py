"""Add Video 5 (倒數計時) as a SECOND ad in each East+Midwest ad set — turning the 1-3-1 into 1-3-2.

Uploads the Drive video once, builds one creative, then creates one ad per existing ad set.
Does not touch the campaign, the ad sets, or the existing Video 2 ads. Idempotent via state.
"""
from __future__ import annotations

from pathlib import Path

from adbot import state
from adbot.commands import drive_client, graph_client
from adbot.logging import final_summary, get_logger
from adbot.settings import load_settings

US_ACCT = "act_921653460987535"   # 【美東美中】MTC X Martin New 6
PAGE_ID = "1180683238455992"
LINK = "https://kidsgrowthformula.com/webinar-main-page"
UTM = "utm_source={{adset.name}}&utm_medium={{placement}}&utm_campaign={{campaign.name}}&utm_content={{ad.name}}"
STATE_KEY = "entities_east_midwest_video5"
STATUS = "ACTIVE"

DRIVE_ID = "1hKjaZh-U-1vPOmoYSD6oXzZqrtLQ9vGw"
AD_NAME = "Video 5：倒數計時"
HEADLINE = "🔴 生長板一閉合，再多錢也追不回來"

ADSETS = {
    "broad": "120254451454690558",
    "FR": "120254451455190558",
    "PE": "120254451455640558",
}

CAPTION = """⏳ 從現在，到你孩子的生長板閉合——你猜，還剩幾年？

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


def main() -> None:
    log = get_logger()
    s = load_settings()
    g = graph_client(s)

    st = state.load(STATE_KEY) or {}
    video_id = st.get("video_id")
    creative_id = st.get("creative_id")
    ads = dict(st.get("ads", {}))

    def persist():
        state.save(STATE_KEY, {"video_id": video_id, "creative_id": creative_id, "ads": ads})

    if not video_id:
        dl = Path("/tmp/east_midwest_v5")
        dl.mkdir(parents=True, exist_ok=True)
        path = dl / "v5_countdown.mp4"
        drive_client(s).download_file(DRIVE_ID, path)
        log.info("downloaded %s (%d bytes)", path, path.stat().st_size)
        video_id = g.upload_video(US_ACCT, str(path), AD_NAME)
        persist()
        log.info("uploaded video -> %s", video_id)

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

    summary = []
    for label, adset_id in ADSETS.items():
        if label in ads:
            continue
        ads[label] = g.create_ad(US_ACCT, name=AD_NAME, adset_id=adset_id,
                                 creative={"creative_id": creative_id}, status=STATUS)["id"]
        persist()
        summary.append(f"  {label:6} adset {adset_id} -> ad {ads[label]}")
        log.info("[%s] created ad %s", label, ads[label])

    log.info("=" * 60)
    for line in summary:
        log.info(line)
    final_summary(log, f"Video 5 added to {len(ads)} ad sets ({STATUS}) — now 1-3-2. "
                       f"video {video_id}, creative {creative_id}.")


if __name__ == "__main__":
    main()
