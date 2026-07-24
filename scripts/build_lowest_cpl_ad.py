"""One-off: add ONE new video ad into the lowest-CPL active ad set, ACTIVE.

Operator asked to put the new creative (北美H4 · Hook 4「去到北美國家，華裔孩子受不了」)
into whichever ad set is currently running the lowest CPL — that is the
'Parents 3–17 + Engaged' ad set (120247164684970259, CPL≈RM78) in campaign
'PNW | SG Winners | 1-1-3 A' (already ACTIVE, CBO). Downloads the Drive video,
uploads it into the US account, builds one ad with the operator-approved caption +
headline + standard UTM url_tags, and activates it. Idempotent via state.
"""
from __future__ import annotations

from pathlib import Path

from adbot import state
from adbot.commands import drive_client, graph_client
from adbot.logging import final_summary, get_logger
from adbot.settings import load_settings

US_ACCT = "act_1629566827721449"
PAGE_ID = "1180683238455992"
LINK = "https://kidsgrowthformula.com/webinar-main-page"
UTM = "utm_source={{adset.name}}&utm_medium={{placement}}&utm_campaign={{campaign.name}}&utm_content={{ad.name}}"
STATE_KEY = "entities_lowest_cpl_ad"

ADSET_ID = "120247164684970259"      # Parents 3–17 + Engaged — lowest CPL (~RM78), campaign PNW | SG Winners | 1-1-3 A
DRIVE_ID = "1lBMz0YuoPnoFKznMbe5hua2ekVqur_7S"
AD_NAME = "Hook 4：去到北美國家，華裔孩子受不了"
HEADLINE = "🔴 去到北美，華裔孩子為什麼開始長不高？"

CAPTION = """⚠️ 去到北美國家，華裔孩子的身體，其實正在「悄悄抗議」。

很多華裔家長以為——孩子來到北美，只是換了個環境而已。

但你有沒有發現……👀
他的飲食、睡眠、運動，全部都變了？
甚至，身高也慢慢地停止增高了？📉

🗣️「可能還在適應吧。」
🗣️「長大一點自然會追上。」
🗣️「同齡的西方孩子本來就比較高啦。」

於是你開始補——🍼 保健品、鈣、各種增高補給，一樣接一樣。
結果呢？📉 身高還是卡著不動，孩子也開始不耐煩。

👉 但問題往往不是「補得不夠」，而是環境一變，孩子的體質先亂了。

馬丁藥師這些年發現，剛移民/長住北美的華裔孩子，最容易卡在這幾點：
🥣 脾胃吸收變差——同樣吃東西，卻吸收不進去
🌿 寒涼飲食 + 氣候，體質偏虛偏寒
😴 作息全亂，深度睡眠不足，生長黃金時段被錯過
🏃 運動型態改變，該長的刺激沒了

💔 而最讓人揪心的是：孩子站在班上，和非亞裔同學一比，那個身高差距，他自己心裡最清楚。

✅ 所以，先別急著補。先看懂孩子在北美「卡在哪一點」，再決定怎麼幫他追高。

👨‍⚕️ 馬丁藥師（台灣執照藥師 · 中西醫結合背景），十多年來服務近 7,000 個家庭，橫跨台灣·馬來西亞·新加坡·香港·美國·加拿大六國——特別了解華裔孩子在北美的成長難題。

這星期，他開一場免費線上公開課——📘《兒童長高方程式》：
📍 為什麼一到北美，孩子的成長就「卡住」
📍 如何從飲食、睡眠、體質，判斷孩子真正的卡點
📍 不同體質的孩子，該怎麼調理才能每年健康長高 6–8cm

⏰ 名額有限，坐滿即止。
👇 點擊下方連結，立即免費報名《兒童長高方程式》

孩子的成長只有一次——別讓「換了環境」，悄悄換走了他本該有的身高。"""


def main() -> None:
    log = get_logger()
    s = load_settings()
    g = graph_client(s)
    drive = drive_client(s)

    st = state.load(STATE_KEY) or {}
    video_id = st.get("video_id")
    ad_id = st.get("ad_id")

    if not video_id:
        dl = Path("/tmp/lowest_cpl_ad")
        dl.mkdir(parents=True, exist_ok=True)
        path = dl / "hook4.mp4"
        drive.download_file(DRIVE_ID, path)
        video_id = g.upload_video(US_ACCT, str(path), AD_NAME)
        st["video_id"] = video_id
        state.save(STATE_KEY, st)
        log.info("uploaded video -> %s", video_id)

    if not ad_id:
        thumb = g.get_video_thumbnail(video_id)
        video_data = {"video_id": video_id, "title": HEADLINE, "message": CAPTION,
                      "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
        if thumb:
            video_data["image_url"] = thumb
        creative = g.create_adcreative(
            US_ACCT, object_story_spec={"page_id": PAGE_ID, "video_data": video_data},
            url_tags=UTM)
        ad = g.create_ad(US_ACCT, name=AD_NAME, adset_id=ADSET_ID,
                         creative={"creative_id": creative["id"]}, status="ACTIVE")
        ad_id = ad["id"]
        st["ad_id"] = ad_id
        state.save(STATE_KEY, st)
        log.info("built ad -> %s (ACTIVE, adset %s)", ad_id, ADSET_ID)

    final_summary(log, f"lowest-CPL ad live: ad {ad_id} in adset {ADSET_ID} (Parents 3-17+Engaged), ACTIVE.")


if __name__ == "__main__":
    main()
