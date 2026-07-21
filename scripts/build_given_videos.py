"""One-off: build 2 new 1-1-2 campaigns' ads from 2 operator-supplied Drive videos.

Campaigns + ad sets are pre-created (Parents 3-17+Engaged / Family & Relationships).
This downloads each Drive video, uploads it into the US ad account, then creates one
ad per (ad set × video) = 4 ads, PAUSED, with the operator's caption + headline + the
standard UTM url_tags. Idempotent via state/entities_given_videos.json.
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
STATE_KEY = "entities_given_videos"

ADSETS = [
    ("A-Parents3-17+Engaged", "120247256176520259"),
    ("B-Family&Relationships", "120247256177010259"),
]

V3_CAPTION = """🚫「我小時候也很矮，後來不也長到這麼高？」

如果你也常這樣安慰自己——請先停一下。

因為現在孩子的成長環境，跟 20 年前已經完全不一樣了。📱

很多爸媽會用自己的經驗，去判斷孩子：
🗣️「男孩子晚一點長很正常。」
🗣️「我以前也是中學才抽高。」
🗣️「再等等看就好了。」

但問題是——❗ 你的孩子，不是 20 年前的你。

馬丁藥師（台灣執照藥師 · 中西醫結合背景）過去十多年來，接觸過來自 🇹🇼🇲🇾🇸🇬🇭🇰🇺🇸🇨🇦 六個國家的家庭，👨‍⚕️ 累積幫助超過上千位正在成長期的孩子。

他發現一件很有意思的事：很多家長不是不關心，反而是「太關心」。知道孩子愛吃什麼、幾點睡、最近做什麼運動——卻從來沒有人教過他們：👉 到底該怎麼看懂孩子真正的「成長訊號」。

😴 有些孩子只是晚發育。⏳ 有些孩子卻正在錯過最重要的成長階段。而這兩種，家長用肉眼幾乎看不出來。

最可惜的是——很多家庭等到發現不對勁的時候，時間已經過去了。💔

但也有一個好消息：發育期不一定是結束，反而可能是孩子最後一次快速成長的關鍵機會。✅ 前提是：你要知道自己在看什麼。

這星期，馬丁藥師特別開放一場免費線上公開課——📘《兒童長高方程式》

課堂上會分享三個大部分家長從沒學過的觀念：
📍 為什麼同樣的方法，別人家孩子有效，你孩子卻沒反應
📍 如何從日常表現，初步判斷孩子的成長狀態與體質
📍 不同孩子在飲食、吸收與成長需求上，到底差在哪裡

你不需要買任何產品，也不需要先做任何決定。但請先把「判斷標準」學會——因為孩子的成長，只有一次。

⏰ 名額有限，先保留位置。
👇 點擊下方鏈接，免費領取《兒童長高方程式》

很多家長最後後悔的，從來不是做錯了什麼，而是當初以為還有時間，一等再等，錯過了黃金期。"""

V4_CAPTION = """⚠️ 孩子長高最大的敵人，不是遺傳——而是「誤判」。

家長們，別再用自己的成長經歷，去預測孩子的未來了。

我知道你會這樣說：
🗣️「不用擔心啦，我以前也是班上最矮的，現在還不是長高了？」

但我想問你一個問題👇 你小時候的成長環境，真的跟孩子現在一樣嗎？

🏃 你小時候放學：跑跳、打球、騎腳車，晚上九點就睡。
📱 現在的孩子：補習、玩手機、十一二點還沒睡。

而且三天兩頭——🤧 鼻子敏感、皮膚過敏、很容易生病，🥣 腸胃吸收也越來越差。

很多父母不知道：孩子長不高，未必是基因問題，❗ 更可能是身體已經出現三個警訊：
😴 睡眠品質不好
🌿 體質差
🦵 筋膜長期緊繃

如果這三個問題沒改善，補品吃再多、牛奶喝再多，效果都很有限。

最可惜的是——很多家長一直等。等一年、等兩年，等到同學一個個抽高，自己的孩子還站在第一排，這時候才開始緊張。💔

我是馬丁藥師。這些年我發現，很多長不高的孩子，問題往往出在「體質」：吸收能力差、長期過敏消耗身體、睡眠品質不好、筋膜長期緊繃——🔍 體質不同，需要的調整方式自然不同。

所以我建立了一套「兒童體質辨識系統」，透過孩子的 👅 舌象、日常症狀、飲食後的身體反應，幫家長找出真正影響成長的關鍵。

這星期，我會開一場免費線上公開課——📘《兒童長高方程式》

課堂上你會瞭解：
📍 為什麼同一種方法，別人孩子有效、你孩子卻沒效
📍 如何從生活細節，判斷孩子的體質特點
📍 不同體質的孩子，飲食與日常調理重點差在哪

如果你的孩子正處於 🔟–1️⃣5️⃣ 歲的關鍵成長階段，別再盲目嘗試各種方法。✅ 先瞭解原因，再決定方向。

⏰ 名額有限，坐滿即止。
👇 點擊下方鏈接，立即免費報名《兒童長高方程式》

孩子的成長只有一次，別讓一個「誤判」，賠掉他的身高。"""

VIDEOS = [
    {"key": "V3", "drive_id": "16rmsI2MjxGcCT8Br7jrXwVGDRBaQo7e3",
     "ad_name": "Video 3：別再拿你的經驗，賭孩子的身高",
     "headline": "🔴 別再拿你的經驗，賭孩子的身高",
     "caption": V3_CAPTION},
    {"key": "V4", "drive_id": "13ztt-jYHTmK7X93Is84GQ1L_8Oc6xd8f",
     "ad_name": "Video 4：孩子長高最大的敵人，不是遺傳而是誤判",
     "headline": "🔴 孩子長高最大的敵人，是遺傳還是誤判？",
     "caption": V4_CAPTION},
]


def main() -> None:
    log = get_logger()
    s = load_settings()
    g = graph_client(s)
    drive = drive_client(s)

    st = state.load(STATE_KEY) or {}
    videos = dict(st.get("videos", {}))   # key -> video_id
    ads = dict(st.get("ads", {}))         # "adset:key" -> ad_id
    dl = Path("/tmp/given_videos")
    dl.mkdir(parents=True, exist_ok=True)

    # 1) upload each video once
    for v in VIDEOS:
        if v["key"] in videos:
            log.info("video %s already uploaded -> %s", v["key"], videos[v["key"]])
            continue
        path = dl / f"{v['key']}.mp4"
        drive.download_file(v["drive_id"], path)
        vid = g.upload_video(US_ACCT, str(path), v["ad_name"])
        videos[v["key"]] = vid
        st = {"videos": videos, "ads": ads}
        state.save(STATE_KEY, st)
        log.info("uploaded %s -> video_id %s", v["key"], vid)

    # 2) one ad per (ad set x video)
    summary = []
    for label, adset_id in ADSETS:
        for v in VIDEOS:
            k = f"{adset_id}:{v['key']}"
            if k in ads:
                summary.append(f"  (skip) {label} / {v['key']} -> {ads[k]}")
                continue
            video_id = videos[v["key"]]
            thumb = g.get_video_thumbnail(video_id)
            video_data = {"video_id": video_id, "title": v["headline"],
                          "message": v["caption"],
                          "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
            if thumb:
                video_data["image_url"] = thumb
            creative = g.create_adcreative(
                US_ACCT, object_story_spec={"page_id": PAGE_ID, "video_data": video_data},
                url_tags=UTM)
            ad = g.create_ad(US_ACCT, name=v["ad_name"], adset_id=adset_id,
                             creative={"creative_id": creative["id"]}, status="PAUSED")
            ads[k] = ad["id"]
            st = {"videos": videos, "ads": ads}
            state.save(STATE_KEY, st)
            summary.append(f"  OK  {label} / {v['key']} -> ad {ad['id']}")
            log.info("built %s / %s -> %s", label, v["key"], ad["id"])

    log.info("=" * 70)
    for line in summary:
        log.info(line)
    final_summary(log, f"given-videos build: {sum(1 for x in summary if x.strip().startswith('OK'))} "
                       f"new ads (2 campaigns x 2 videos, PAUSED).")


if __name__ == "__main__":
    main()
