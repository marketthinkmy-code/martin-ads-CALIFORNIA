"""Build the first campaigns in the NEW ad account (act_2022836788419850, USD).

Operator decisions (2026-09-26): mirror the East+Midwest naming, run only the four
creatives with real US paid sales, two audience campaigns (Parents / F&R), Broad off,
one video per ad set, US$12/day per ad set (≈RM50), built PAUSED.

  US East+Midwest | Parents 3-17 + Engaged | Proven 4      US East+Midwest | Family and Relationships | Proven 4
    ad set · Video 1 华人孩子        $12                        (same four)
    ad set · 15-16-17歲孩子           $12
    ad set · 15歲以上還有機會長高嗎   $12
    ad set · 林書豪story              $12

Identity = Page 馬丁藥師｜兒童身高管理專家 + IG martinyaoshi.us (resolved from the Page).

Creatives use the EXISTING Page posts of the four winners (object_story_id) so likes and
comments keep accumulating on one post across accounts — the operator's call. Only if a
post id cannot be used does a slot fall back to re-uploading the video with the 醫師 /
10,000 位孩子 copy. Ad NAMES are kept identical to the original winners so UTM attribution
in the paid sheet stays continuous. Region keys resolved live. Idempotent by name.
"""
from __future__ import annotations

import json
from pathlib import Path

import requests

from adbot.commands import graph_client
from adbot.logging import final_summary, get_logger
from adbot.newbm import NEW_ACCT, new_bm_client
from adbot.settings import load_settings

PAGE_ID = "1180683238455992"
PIXEL_ID = "2035639583602118"
LINK = "https://kidsgrowthformula.com/us-register"
UTM = "utm_source={{adset.name}}&utm_medium={{placement}}&utm_campaign={{campaign.name}}&utm_content={{ad.name}}"
DAILY_CENTS = 1200                 # US$12.00/day per AD SET (account currency is USD)
STATUS = "PAUSED"
AGE_MIN, AGE_MAX = 35, 65
EXCLUDE_NAME = "[NEW 美东美中 US] 15days complete registration"
BATCH = "Proven 4"

EAST = ["New York", "New Jersey", "Massachusetts", "Pennsylvania",
        "Connecticut", "Maryland", "Virginia"]
MIDWEST = ["Illinois", "Michigan", "Ohio", "Minnesota"]

CAP_V1 = """👨‍🏫 在美國的華人孩子，為什麼特別難長高？
不是基因，是環境。

尤其適合這些家長：
🛑 孩子一年長不到 6cm
🛑 骨齡超前，或落後
🛑 有性早熟跡象
🛑 睡不好、注意力不集中
🛑 課業壓力大，身高停住了

大家好，我是馬丁醫師 🧑🏻‍⚕️🇹🇼
台灣執照醫師，超過 10 年中西醫學經驗
已經幫助超過 10,000 位孩子健康長高
其中很多，是被醫生判定「不會再長」的

放心，我自己也是爸爸
❌ 不用藥、不打針
❌ 不逼孩子吃難吃的東西
❌ 不要求拼命運動
只用簡單、科學、家裡就能做的方法

📌 免費線上分享會，你會學到：
✅ 5–17 歲，黃金長高期到底在哪
✅ 怎麼管理身高，不錯過關鍵點
✅ 哪些營養和運動真的有效
✅ 成長金三角：身高 × 睡眠 × 注意力

⚠️ 別讓身高，成為孩子一輩子的遺憾
👇 點擊下方，免費報名"""

CAP_1517 = """😰 孩子 15、16、17 歲，已經停止長高一陣子了？
有件事，現在一定要告訴你。

孩子已經進入「補救期」
再不管，就真的定型了。

其實男孩保守可以長到 20 歲
有些到 23 歲
女孩初經來後，大約還能再長五年

但如果這個年紀停了
又沒有任何補救
身高很可能就永遠停在現在

大家好，我是馬丁醫師 🧑🏻‍⚕️🇹🇼
台灣執照醫師，超過 10 年中西醫學經驗
已經幫助超過 10,000 位孩子健康長高

📍 補救期怎麼抓、怎麼調
我會在免費線上分享會裡講給你聽

✅ 15 歲以後還剩多少空間
✅ 怎麼管理身高，不錯過最後關鍵點
✅ 哪些營養和運動真的有效
✅ 成長金三角：身高 × 睡眠 × 注意力

⚠️ 現在行動，還來得及
👇 點擊下方，免費報名"""

CAP_15UP = """📏 「15 歲就太晚了，長不高了」？
❌ 錯。孩子還在「隱藏的長高期」。

很多爸媽都以為
孩子 16、17 歲，身高差不多定型了
但我想告訴你：
👉 男生可以長到 20 歲
👉 女生至少還有一年成長空間

這個階段，專業上叫「居久期」
❗ 什麼都不做，孩子確實幾乎不長
✅ 但只要做對管理，還是能繼續長

大家好，我是馬丁醫師 🧑🏻‍⚕️🇹🇼
台灣執照醫師，超過 10 年中西醫學經驗
已經幫助超過 10,000 位孩子健康長高
其中不少是「15 歲以上還再長 3–5cm」的真實案例

📌 想在居久期逆勢長高，兩件事要做到：
1️⃣ 孩子自己真的想長高
2️⃣ 爸媽懂得管理體質、睡眠、飲食和運動節奏

📣 我特別為 15–17 歲家長準備了一場免費線上分享會
✅ 15 歲以後還剩多少空間
✅ 怎麼管理身高，不錯過最後關鍵點
✅ 哪些營養和運動真的有效
✅ 成長金三角：身高 × 睡眠 × 注意力

⚠️ 別因為「以為太晚了」就放棄
👉 現在做對，孩子還有最後一波衝刺機會
👇 點擊下方，免費報名"""

CAP_LIN = """👨‍🏫 你家孩子 5–17 歲，一年長不到 5cm？
我可以幫到你。

你試過：
✔ 早睡、多跑步、喝牛奶
✔ 買了各種鈣片和保健品
✔ 看過兒科醫生，說「再等等看」
✔ 試過偏方，還是沒變化

結果還是一樣
孩子站在同學旁邊，還是最矮的

大家好，我是馬丁醫師 🧑🏻‍⚕️🇹🇼
台灣執照醫師，超過 10 年中西醫學經驗
已經幫助超過 10,000 位孩子健康長高
其中很多，是被醫生判定「不會再長」的

放心，我自己也是爸爸
❌ 不用藥、不打針
❌ 不逼孩子吃難吃的東西
❌ 不要求拼命運動

我用的是經過 10,000 位孩子驗證的方法：
身高 × 睡眠 × 注意力，三個維度一起調

📌 免費線上分享會，你會學到：
✅ 5–17 歲，黃金長高期到底在哪
✅ 怎麼管理身高，不錯過關鍵點
✅ 哪些營養和運動真的有效
✅ 成長金三角：身高 × 睡眠 × 注意力

⚠️ 別讓身高，成為孩子一輩子的遺憾
👇 點擊下方，免費報名"""

# source video ids live in the East+Midwest account; ad names are the UTM attribution keys
VIDEOS = [
    {"key": "V1",   "src_video": "2013939992693198", "post_id": "1180683238455992_122134716117351616",
     "ad_name": "Video 1: 华人孩子在美国很难长高",
     "short": "Video 1 华人孩子", "headline": "🔴 想讓孩子健康長高？我可以幫助你！", "caption": CAP_V1},
    {"key": "V1517", "src_video": "2635916286878637", "post_id": "1180683238455992_122134932705351616",
     "ad_name": "Video: 15-16-17歲孩子",
     "short": "15-16-17歲孩子", "headline": "🔴 孩子 15、16、17 歲還沒抽高？補救期就剩現在", "caption": CAP_1517},
    {"key": "V15UP", "src_video": "1927105534653150", "post_id": "1180683238455992_122134715961351616",
     "ad_name": "Video: 孩子15歲以上還有機會長高嗎?",
     "short": "15歲以上還有機會長高嗎", "headline": "🔴 想讓孩子健康長高？我可以幫助你！", "caption": CAP_15UP},
    {"key": "LIN",  "src_video": "1478933497330796", "post_id": "1180683238455992_122134932717351616",
     "ad_name": "MAR Video 5: 林書豪story",
     "short": "林書豪story", "headline": "🔴 想讓孩子健康長高？我可以幫助你！", "caption": CAP_LIN},
]


def resolve_regions(g, log, names):
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


def existing_by_name(g, edge, names_field="name"):
    rows = g._get_all(f"{NEW_ACCT}/{edge}", {"fields": f"id,{names_field}", "limit": 200})
    return {r.get(names_field): r["id"] for r in rows}


def main() -> None:
    log = get_logger()
    old = graph_client(load_settings())   # reads the source videos in East+Midwest
    new = new_bm_client()                 # writes into the new account

    # hard gates — do not build a half-configured account
    px = new._request("GET", f"{NEW_ACCT}/adspixels", params={"fields": "id"}).get("data", [])
    if not any(str(p["id"]) == PIXEL_ID for p in px):
        raise SystemExit(f"pixel {PIXEL_ID} not on {NEW_ACCT} — share it first")
    auds = existing_by_name(new, "customaudiences")
    if EXCLUDE_NAME not in auds:
        raise SystemExit(f"exclusion audience {EXCLUDE_NAME!r} missing — run setup after accepting "
                         f"the Custom Audience ToS")
    exclude = [{"id": auds[EXCLUDE_NAME]}]
    log.info("gates passed: pixel ok, exclusion audience %s", exclude[0]["id"])

    regions = resolve_regions(new, log, EAST + MIDWEST)
    base = {"age_min": AGE_MIN, "age_max": AGE_MAX,
            "geo_locations": {"regions": regions, "location_types": ["home", "recent"]},
            "locales": [20, 21, 22], "excluded_custom_audiences": exclude,
            "targeting_automation": {"advantage_audience": 0}}
    AUDIENCES = [
        {"key": "PE", "name": "Parents 3-17 + Engaged",
         "targeting": {**base, "flexible_spec": [{
             "interests": [{"id": 6003263791114}, {"id": 6003346592981}],
             "behaviors": [{"id": 6071631541183}],
             "family_statuses": [{"id": 6023005529383}, {"id": 6023005570783},
                                 {"id": 6023005681983}, {"id": 6023080302983}]}]}},
        {"key": "FR", "name": "Family and Relationships",
         "targeting": {**base, "flexible_spec": [{"interests": [
             {"id": 6002991239659}, {"id": 6003101323797}, {"id": 6003232518610},
             {"id": 6003409392877}, {"id": 6003445506042}, {"id": 6003476182657},
             {"id": 6004100985609}]}]}},
    ]

    # identity: Page + the IG account linked to it (ad-account IG listing is empty, the
    # link lives on the Page)
    ig_id = None
    try:
        pg = new.get_object(PAGE_ID, "instagram_business_account,connected_instagram_account")
        ig = pg.get("instagram_business_account") or pg.get("connected_instagram_account") or {}
        ig_id = ig.get("id")
    except Exception as e:  # noqa: BLE001
        log.info("could not read IG from Page: %s", e)
    log.info("identity: page %s · instagram_user_id %s", PAGE_ID, ig_id or "(none — page-backed)")

    # 1) one creative per winner. Existing post first (engagement carries over); fall back to
    #    re-uploading the video with the new copy only if the post cannot be used.
    have_creatives = existing_by_name(new, "adcreatives")
    have_videos = existing_by_name(new, "advideos", "title")
    dl = Path("/tmp/new_acct_proven4"); dl.mkdir(parents=True, exist_ok=True)
    creatives, modes = {}, {}
    for v in VIDEOS:
        k, title = v["key"], v["ad_name"]
        if title in have_creatives:
            creatives[k] = have_creatives[title]; modes[k] = "existing"
            log.info("[%s] creative already exists: %s", k, creatives[k])
            continue
        fields = {"name": title, "object_story_id": v["post_id"], "url_tags": UTM}
        if ig_id:
            fields["instagram_user_id"] = ig_id
        try:
            creatives[k] = new.create_adcreative(NEW_ACCT, **fields)["id"]; modes[k] = "post"
            log.info("[%s] created creative from existing post %s -> %s", k, v["post_id"], creatives[k])
            continue
        except Exception as e:  # noqa: BLE001
            log.info("[%s] existing post unusable (%s) — falling back to new video creative", k, e)
        if title in have_videos:
            vid = have_videos[title]
        else:
            src = old.get_object(v["src_video"], "source")["source"]
            path = dl / f"{k}.mp4"
            with requests.get(src, stream=True, timeout=300) as r:
                r.raise_for_status()
                with open(path, "wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        fh.write(chunk)
            log.info("[%s] downloaded %d bytes from East+Midwest", k, path.stat().st_size)
            vid = new.upload_video(NEW_ACCT, str(path), title)
            log.info("[%s] uploaded -> %s", k, vid)
        video_data = {"video_id": vid, "title": v["headline"], "message": v["caption"],
                      "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
        thumb = new.get_video_thumbnail(vid)
        if thumb:
            video_data["image_url"] = thumb
        spec = {"page_id": PAGE_ID, "video_data": video_data}
        if ig_id:
            spec["instagram_user_id"] = ig_id
        creatives[k] = new.create_adcreative(NEW_ACCT, name=title, object_story_spec=spec,
                                             url_tags=UTM)["id"]; modes[k] = "new"
        log.info("[%s] created NEW video creative %s", k, creatives[k])

    # 2) one campaign per audience; one ad set per video; ad set named after targeting
    have_campaigns = existing_by_name(new, "campaigns")
    summary, n_adsets, n_ads = [], 0, 0
    for aud in AUDIENCES:
        cname = f"US East+Midwest | {aud['name']} | {BATCH}"
        if cname in have_campaigns:
            cid = have_campaigns[cname]
            log.info("[%s] campaign exists: %s", aud["key"], cid)
        else:
            cid = new.create_campaign(
                NEW_ACCT, name=cname, objective="OUTCOME_SALES", buying_type="AUCTION",
                status=STATUS, special_ad_categories=[],
                is_adset_budget_sharing_enabled=False)["id"]
            log.info("[%s] created campaign %s", aud["key"], cid)
        have_adsets = {r["name"]: r["id"] for r in new._get_all(
            f"{cid}/adsets", {"fields": "id,name", "limit": 100})}
        for v in VIDEOS:
            asname = f"{aud['name']} · {v['short']}"
            if asname in have_adsets:
                asid = have_adsets[asname]
                log.info("  ad set exists: %s", asname)
            else:
                asid = new.create_adset(
                    NEW_ACCT, campaign_id=cid, name=asname,
                    daily_budget=DAILY_CENTS, bid_strategy="LOWEST_COST_WITHOUT_CAP",
                    optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                    promoted_object={"pixel_id": PIXEL_ID,
                                     "custom_event_type": "COMPLETE_REGISTRATION"},
                    targeting=aud["targeting"], status=STATUS)["id"]
                n_adsets += 1
            have_ads = {r["name"] for r in new._get_all(f"{asid}/ads", {"fields": "id,name"})}
            if v["ad_name"] in have_ads:
                continue
            adid = new.create_ad(NEW_ACCT, name=v["ad_name"], adset_id=asid,
                                 creative={"creative_id": creatives[v["key"]]},
                                 status=STATUS)["id"]
            n_ads += 1
            summary.append(f"  {aud['key']}:{v['key']:6} adset {asid} -> ad {adid}")

    log.info("=" * 60)
    for line in summary:
        log.info(line)
    final_summary(log, f"NEW account Proven-4 built ({STATUS}, US$12/day × 8 ad sets = US$96/day): "
                       f"{n_adsets} new ad sets, {n_ads} new ads · creative modes {modes} · "
                       f"IG {ig_id or 'page-backed'}")


if __name__ == "__main__":
    main()
