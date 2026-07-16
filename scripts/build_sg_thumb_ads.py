"""Build the 3 SG-winner ads whose cross-account video thumbnails couldn't be
ingested inline (top-seller 正常健康的孩子, 运动, Eunice 见证).

Fix: for each SG video, pull its Meta-generated thumbnail via the /thumbnails edge
(works cross-account with the system-user token), download it, re-upload it into the
US ad account to get a US-owned image_hash, then create the video creative with that
hash. Ads go into the existing "PNW | SG Winners" ad set, PAUSED.

Idempotent: records created ids in state/entities_sg_thumb_ads.json; a re-run that
finds an ad already built for a video skips it.
"""
from __future__ import annotations

import os
import tempfile

import requests

from adbot import state
from adbot.commands import graph_client
from adbot.logging import final_summary, get_logger
from adbot.settings import load_settings

US_ACCT = "act_1629566827721449"
PAGE_ID = "1180683238455992"
ADSET_ID = "120247164684970259"
LINK = "https://kidsgrowthformula.com/webinar-main-page"
STATE_KEY = "entities_sg_thumb_ads"

# (ad name, SG video_id, 繁体 caption) — milk/bread already excluded upstream
ADS = [
    ("SG#1 Video 2 一个3～15岁正常健康的孩子", "1228993401589348",
     "一個3～15歲、看起來正常健康的孩子，也可能正在悄悄長不高。方向對了才有機會。點擊了解 »"),
    ("SG#11 Video Hook 2 运动但是没长高", "1162587834838900",
     "孩子一直在運動，卻還是沒長高？也許問題不在運動量，而在方向錯了。點擊了解 »"),
    ("SG#13 见证1 短头发 Eunice Ngu", "1524241481596749",
     "【真實家長見證】跟著調整生活與體質，孩子的改變，家長看得見。點擊了解 »"),
]


def main() -> None:
    log = get_logger()
    s = load_settings()
    g = graph_client(s)

    existing = state.load(STATE_KEY) or {}
    done = dict(existing.get("ads", {}))          # video_id -> ad_id
    summary = []

    for name, video_id, message in ADS:
        if video_id in done:
            log.info("skip %s (already built ad %s)", name, done[video_id])
            summary.append(f"  (skip) {name} -> {done[video_id]}")
            continue

        thumb = g.get_video_thumbnail(video_id)
        if not thumb:
            log.error("!! no thumbnail for video %s (%s) — SKIP", video_id, name)
            summary.append(f"  FAIL  {name}: no /thumbnails uri")
            continue

        # download the Meta thumbnail and re-upload it into the US account
        r = requests.get(thumb, timeout=60)
        r.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as fh:
            fh.write(r.content)
            tmp = fh.name
        try:
            image_hash = g.upload_image(US_ACCT, tmp)
        finally:
            os.unlink(tmp)
        log.info("%s: video %s -> US image_hash %s", name, video_id, image_hash)

        story = {"page_id": PAGE_ID, "video_data": {
            "video_id": video_id, "image_hash": image_hash, "message": message,
            "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}}
        creative = g.create_adcreative(US_ACCT, object_story_spec=story)
        ad = g.create_ad(US_ACCT, name=name, adset_id=ADSET_ID,
                         creative={"creative_id": creative["id"]}, status="PAUSED")
        done[video_id] = ad["id"]
        state.save(STATE_KEY, {"ads": done})
        log.info("   built ad %s", ad["id"])
        summary.append(f"  OK    {name} -> {ad['id']}")

    log.info("═" * 70)
    for line in summary:
        log.info(line)
    final_summary(log, f"SG thumbnail ads built: {sum(1 for l in summary if l.strip().startswith('OK'))} "
                       f"new (ad set {ADSET_ID}, PAUSED).")


if __name__ == "__main__":
    main()
