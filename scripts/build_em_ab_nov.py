"""Build the US East+Midwest weekly-funnel A/B test (live session 2026-11-18, EST).

Same structure as the US West build (scripts/build_west_ab_nov.py), operator-approved
2026-11-06: one campaign per (geo level x audience), three ad sets per campaign, one bilingual
video each, ABO RM50/day per ad set, built PAUSED. 6 x 3 = 18 ad sets = RM900/day.

  州级  = NY, NJ, MA, MD, MI, OH, IN + Ontario, EXCLUDING the 城市级 cities (no overlap)
  城市级 = the 9 Doc cities + Toronto
  Advantage+ audience: 城市级 ON (age 25-65, 35-65 suggested), 州级 OFF (age 35-65) — as West
  Exclusions: [美東美中 US] 15days complete registration only (operator: no paid list here)
  Videos: the same V1/V3/V4 bilingual uploads, attached from the 加州 account by video id.

Idempotent by name; rules in docs/rules/us-weekly-funnel.md.
"""
from __future__ import annotations

import json
import time

from adbot.commands import graph_client
from adbot.settings import load_settings

ACCT = "act_921653460987535"           # 美東美中 (account tz America/New_York)
PAGE_ID = "1180683238455992"           # 馬丁藥師｜兒童身高管理專家
IG_USER_ID = "17841415309062626"       # martinyaoshi.us
PIXEL_ID = "2035639583602118"
LINK = "https://kidsgrowthformula.com/us-register"
UTM = ("utm_source={{adset.name}}&utm_medium={{placement}}"
       "&utm_campaign={{campaign.name}}&utm_content={{ad.name}}")
DAILY = 5000                           # RM50.00 per ad set
STATUS = "PAUSED"
EXCLUDE = [{"id": "120254451454000558"}]   # [美東美中 US] 15days complete registration

HEADLINE = "🔴 想讓孩子健康長高？我可以幫助你！"
BODY = """👨‍🏫 想讓孩子健康長高？我可以幫助你！

尤其適合給：
🛑 孩子一年長不到 6cm 的家長
🛑 骨齡超前 / 落後孩子的家長
🛑 性早熟孩子的家長
🛑 注意力不集中孩子的家長
🛑 睡眠障礙的孩子的家長
🛑 課業壓力長不高的孩子的家長

大家好，我是馬丁醫師 🧑🏻‍⚕️🇹🇼
來自台灣的兒童長高專家，擁有超過 10 年中西醫學經驗

🌍 我已經幫助來自台灣、馬來西亞、曼谷、澳洲、
加拿大和美國等國家的10,000+名孩子，每年實現健康增高6cm-8cm！
這些孩子中，有很多被傳統醫生認為難以再長高的，
但在我的指導下，他們實現了健康增高的夢想！🌈

💡 如果你：
👉 擔心孩子因父母基因遺傳，難以再長高
👉 嘗試了很多網上的偏方、保健品、運動，孩子還是沒長高
👉 看了很多中醫、西醫做調理，但都不見效

放心！作為一位父親，我深知家長的心情。🫂
❌ 我絕對不會使用藥物或不自然的方法，
❌ 也不會逼迫孩子吃各種難以下嚥的食物，
❌ 更不會要求他們拼命運動。

相反，我會教你一些簡單、健康、科學認證的方法，
讓你能夠關注孩子身心靈發展的同時，幫助他們健康增高！✨

✨ 如果你想知道我如何幫助這些孩子實現增高目標，歡迎參加我的線上課程！

💡 在這堂線上課中，你將學習：
✅ 孩子的黃金長高期是什麼時候？
✅ 如何科學管理孩子的身高，避免錯過成長關鍵點？
✅ 哪些營養、運動最有效，幫孩子輕鬆增高？
✅ 無需額外花費時間和精力，讓增高變得簡單
✅ 成長金三角：管理身高、注意力、睡眠

⚠️ 抓住這個機會，不要讓身高問題成為孩子一輩子的遺憾！
點擊以下 Button 報名，讓我幫助你的孩子擁有一個不後悔的童年！我們課程見！👋

#兒童長高方程式 #兒童長高 #長高 #馬丁醫師 #注意力 #成長 #學習力 #馬丁醫師 #身高 #孩子 #馬丁醫師 #霸凌 #頂嘴 #家庭教養 #家庭教育 #親子關係"""

# Bilingual uploads already in the 加州 account (build_west_ab_nov run 2, 2026-11-04);
# cross-account attach by video id is proven for these two accounts (handoff note 8).
VIDEOS = [
    {"key": "V1", "video_id": "1383850263581922", "ad_name": "Video 1：华人孩子在美国很难长高（双语）"},
    {"key": "V3", "video_id": "2610115166079240", "ad_name": "Video 3：孩子要長到175以上（双语）"},
    {"key": "V4", "video_id": "2608819096298587", "ad_name": "Video 4：吃饭喝水，咬咬吞（双语）"},
]

AUDIENCES = [
    {"key": "PE", "name": "Parents 3-17 + Engaged", "flex": [{
        "interests": [{"id": 6003263791114}, {"id": 6003346592981}],
        "behaviors": [{"id": 6071631541183}],
        "family_statuses": [{"id": 6023005529383}, {"id": 6023005570783},
                            {"id": 6023005681983}, {"id": 6023080302983}]}]},
    {"key": "FR", "name": "Family and Relationships", "flex": [{"interests": [
        {"id": 6002991239659}, {"id": 6003101323797}, {"id": 6003232518610},
        {"id": 6003409392877}, {"id": 6003445506042}, {"id": 6003476182657},
        {"id": 6004100985609}]}]},
    {"key": "BR", "name": "Broad", "flex": None},
]


# Resolved live with adbot-geo-search on 2026-11-06 (see commit message for the read-back).
STATE_REGIONS = [{"key": k} for k in [
    "3875",   # New York
    "3873",   # New Jersey
    "3864",   # Massachusetts
    "3863",   # Maryland
    "3865",   # Michigan
    "3878",   # Ohio
    "3857",   # Indiana
    "533",    # Ontario (CA)
]]
CITY_GEO = {
    "cities": [{"key": k} for k in [
        "2673814",  # West Windsor, NJ
        "2483571",  # East Brunswick, NJ
        "2484711",  # Princeton, NJ
        "2465628",  # Lexington, MA
        "2462863",  # Rockville, MD
        "2462511",  # Potomac, MD
        "296875",   # Toronto, ON
    ]],
    # Queens areas are neighbourhoods in Meta, not cities
    "neighborhoods": [{"key": k} for k in [
        "2487118",  # Bayside, NY
        "2488666",  # Fresh Meadows, NY
        "2488566",  # Flushing, NY
    ]],
}


def throttle_tolerant(g):
    """Wrap g._request so a Meta rate-limit error waits it out instead of killing the build."""
    from adbot.clients import graph as graph_mod
    raw = g._request

    def wrapped(*a, **kw):
        for attempt in range(8):
            try:
                return raw(*a, **kw)
            except graph_mod._Retryable as e:
                if "throttle" not in str(e).lower() and "limit" not in str(e).lower():
                    raise
                print(f"  rate-limited ({str(e)[:70]}) — sleeping 5 min [{attempt + 1}/8]", flush=True)
                time.sleep(300)
        return raw(*a, **kw)

    g._request = wrapped
    return g


def existing(g, edge, field="name"):
    return {r.get(field): r["id"] for r in g._get_all(f"{ACCT}/{edge}",
                                                       {"fields": f"id,{field}", "limit": 200})}


def throttle_tolerant(g):
    """Wrap g._request so a Meta rate-limit error waits it out instead of killing the build."""
    from adbot.clients import graph as graph_mod
    raw = g._request

    def wrapped(*a, **kw):
        for attempt in range(8):
            try:
                return raw(*a, **kw)
            except graph_mod._Retryable as e:  # raised after tenacity's own short retries
                if "throttle" not in str(e).lower() and "limit" not in str(e).lower():
                    raise
                print(f"  rate-limited ({str(e)[:70]}) — sleeping 5 min [{attempt + 1}/8]", flush=True)
                time.sleep(300)
        return raw(*a, **kw)

    g._request = wrapped
    return g


def targeting(level, aud):
    t = {"geo_locations": level["geo"], "locales": [20, 21, 22],
         "excluded_custom_audiences": EXCLUDE}
    if level["advantage"]:
        t.update({"age_min": 25, "age_max": 65, "age_range": [35, 65],
                  "targeting_automation": {"advantage_audience": 1}})
    else:
        t.update({"age_min": 35, "age_max": 65, "targeting_automation": {"advantage_audience": 0}})
    if level["exclude_geo"]:
        t["excluded_geo_locations"] = level["exclude_geo"]
    if aud["flex"]:
        t["flexible_spec"] = aud["flex"]
    return t


def main() -> None:
    s = load_settings()
    g = throttle_tolerant(graph_client(s))
    levels = [
        {"label": "州级", "adset_tag": "州级 7州+Ontario", "advantage": False,
         "geo": {"regions": STATE_REGIONS, "location_types": ["home", "recent"]},
         "exclude_geo": CITY_GEO},
        {"label": "城市级", "adset_tag": "城市级 9 cities+Toronto", "advantage": True,
         "geo": {**CITY_GEO, "location_types": ["home", "recent"]},
         "exclude_geo": None},
    ]

    print("== creatives ==", flush=True)
    have_cr = existing(g, "adcreatives")
    creative = {}
    for v in VIDEOS:
        if v["ad_name"] in have_cr:
            creative[v["key"]] = have_cr[v["ad_name"]]
            print(f"  {v['key']} creative exists {creative[v['key']]}")
            continue
        vd = {"video_id": v["video_id"], "title": HEADLINE, "message": BODY,
              "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
        thumb = g.get_video_thumbnail(v["video_id"])
        if thumb:
            vd["image_url"] = thumb
        spec = {"page_id": PAGE_ID, "instagram_user_id": IG_USER_ID, "video_data": vd}
        creative[v["key"]] = g.create_adcreative(ACCT, name=v["ad_name"],
                                                 object_story_spec=spec, url_tags=UTM)["id"]
        time.sleep(2)
        print(f"  {v['key']} creative {creative[v['key']]} (IG martinyaoshi.us)", flush=True)

    print("== campaigns / ad sets / ads ==", flush=True)
    have_c = existing(g, "campaigns")
    n_ads = 0
    for lvl in levels:
        for aud in AUDIENCES:
            cname = f"US East+Midwest | {lvl['label']} | {aud['name']}"
            cid = have_c.get(cname) or g.create_campaign(
                ACCT, name=cname, objective="OUTCOME_SALES", buying_type="AUCTION",
                status=STATUS, special_ad_categories=[],
                is_adset_budget_sharing_enabled=False)["id"]
            print(f"  campaign {cid}  {cname}", flush=True)
            time.sleep(3)
            have_as = {r["name"]: r["id"] for r in g._get_all(f"{cid}/adsets", {"fields": "id,name"})}
            for v in VIDEOS:
                asname = f"{aud['name']} | {lvl['adset_tag']} | {v['key']}"
                existed = asname in have_as
                asid = have_as.get(asname) or g.create_adset(
                    ACCT, campaign_id=cid, name=asname, daily_budget=DAILY,
                    bid_strategy="LOWEST_COST_WITHOUT_CAP",
                    optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                    promoted_object={"pixel_id": PIXEL_ID, "custom_event_type": "COMPLETE_REGISTRATION"},
                    targeting=targeting(lvl, aud), status=STATUS)["id"]
                time.sleep(3)
                have_ads = ({r["name"] for r in g._get_all(f"{asid}/ads", {"fields": "name"})}
                            if existed else set())
                if v["ad_name"] not in have_ads:
                    adid = g.create_ad(ACCT, name=v["ad_name"], adset_id=asid,
                                       creative={"creative_id": creative[v["key"]]},
                                       status=STATUS)["id"]
                    n_ads += 1
                    time.sleep(3)
                    print(f"    adset {asid} {asname} -> ad {adid}", flush=True)
                else:
                    print(f"    adset {asid} {asname} (ad exists)", flush=True)
    print(f"DONE — {n_ads} new ads, all {STATUS}")


if __name__ == "__main__":
    main()
