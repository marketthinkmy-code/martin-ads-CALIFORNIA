"""Build the US West weekly-funnel A/B test (live session 2026-11-11, PST).

Operator-approved structure (2026-11-04): one campaign per (geo level × audience), three
ad sets per campaign — one bilingual video each, ABO RM50/day per ad set, built PAUSED.

  州级  = whole California + Washington, EXCLUDING the 9 Doc cities (no audience overlap)
  城市级 = only the 9 Doc cities
  audiences = Parents 3-17 + Engaged · Family and Relationships · Broad
  videos    = Video 1 华人孩子 · Video 3 175以上 · Video 4 吃饭喝水 (bilingual re-cuts)

6 campaigns × 3 ad sets = 18 ad sets = RM900/day. Rules: docs/rules/us-weekly-funnel.md.
City and state keys are resolved live from Meta search and printed for verification.
Each video is uploaded once and its creative reused by all six campaigns. Idempotent by
name, so a failed run can simply be re-run.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from adbot.commands import drive_client, graph_client
from adbot.settings import load_settings

ACCT = "act_1629566827721449"          # 【加州】MTC X Martin New 5 (MYR, account tz Asia/KL)
PAGE_ID = "1180683238455992"           # 馬丁藥師｜兒童身高管理專家
IG_USER_ID = "36101311622850677"       # martinyaoshi.us — dropped automatically if Meta rejects it
PIXEL_ID = "1921735088376759"
LINK = "https://kidsgrowthformula.com/register"
UTM = ("utm_source={{adset.name}}&utm_medium={{placement}}"
       "&utm_campaign={{campaign.name}}&utm_content={{ad.name}}")
DAILY = 5000                           # RM50.00 per ad set
STATUS = "PAUSED"
# 15-day registrants + every US paid-student list in this account
EXCLUDE = [{"id": "120236056842490259"}, {"id": "120240867576290259"},
           {"id": "120243775674560259"}, {"id": "120247871985980259"}]

STATES = ["California", "Washington"]
CITIES = [("Cupertino", "California"), ("Fremont", "California"), ("Arcadia", "California"),
          ("Irvine", "California"), ("Walnut", "California"), ("Saratoga", "California"),
          ("Milpitas", "California"), ("Bellevue", "Washington"), ("Redmond", "Washington")]

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

# Drive file -> video, as confirmed by the operator (file names are random)
VIDEOS = [
    {"key": "V1", "drive_id": "1DzK-IZvMm_iRyavhFHnh_qd0_QblRmzk",
     "ad_name": "Video 1：华人孩子在美国很难长高（双语）"},
    {"key": "V3", "drive_id": "10Dxe7bZTjX3Cg3YxDxROiQ4BPDLt7bjP",
     "ad_name": "Video 3：孩子要長到175以上（双语）"},
    {"key": "V4", "drive_id": "1A7IivhuyGW1lW98Cw_8D9va2Yyeqlb14",
     "ad_name": "Video 4：吃饭喝水，咬咬吞（双语）"},
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


def search_geo(g, q, kind):
    res = g._request("GET", "search", params={
        "type": "adgeolocation", "location_types": json.dumps([kind]),
        "q": q, "country_code": "US", "limit": 10})
    return res.get("data", [])


def resolve(g):
    states = []
    for name in STATES:
        hit = next((r for r in search_geo(g, name, "region") if r.get("name") == name), None)
        if not hit:
            raise SystemExit(f"region not found: {name}")
        states.append({"key": str(hit["key"])})
        print(f"  region {name:12} -> {hit['key']}")
    cities = []
    for name, region in CITIES:
        hit = next((r for r in search_geo(g, name, "city")
                    if r.get("name") == name and r.get("region") == region), None)
        if not hit:
            raise SystemExit(f"city not found: {name}, {region}")
        cities.append({"key": str(hit["key"])})
        print(f"  city   {name:12} {region:10} -> {hit['key']}")
    return states, cities


def existing(g, edge, field="name"):
    return {r.get(field): r["id"] for r in g._get_all(f"{ACCT}/{edge}",
                                                       {"fields": f"id,{field}", "limit": 200})}


def main() -> None:
    s = load_settings()
    g = graph_client(s)

    print("== geo ==")
    states, cities = resolve(g)
    geo_levels = [
        {"key": "STATE", "label": "州级", "adset_tag": "州级 CA+WA",
         "geo": {"regions": states, "location_types": ["home", "recent"]},
         "exclude_geo": {"cities": cities}},
        {"key": "CITY", "label": "城市级", "adset_tag": "城市级 9 cities",
         "geo": {"cities": cities, "location_types": ["home", "recent"]},
         "exclude_geo": None},
    ]

    ig_id = None
    try:
        pg = g.get_object(PAGE_ID, "instagram_business_account,connected_instagram_account")
        ig_id = ((pg.get("instagram_business_account") or pg.get("connected_instagram_account"))
                 or {}).get("id")
    except Exception as e:  # noqa: BLE001
        print(f"  page IG lookup failed: {str(e)[:90]}")
    print(f"  IG from page: {ig_id or 'none — page-backed'}")

    print("== videos / creatives ==")
    have_vid = existing(g, "advideos", "title")
    have_cr = existing(g, "adcreatives")
    dl = Path("/tmp/west_ab"); dl.mkdir(exist_ok=True)
    creative, ig_ok = {}, bool(ig_id)
    for v in VIDEOS:
        if v["ad_name"] in have_cr:
            creative[v["key"]] = have_cr[v["ad_name"]]
            print(f"  {v['key']} creative exists {creative[v['key']]}")
            continue
        vid = have_vid.get(v["ad_name"])
        if not vid:
            path = dl / f"{v['key']}.mov"
            drive_client(s).download_file(v["drive_id"], path)
            print(f"  {v['key']} downloaded {path.stat().st_size/1e6:.1f}MB")
            vid = g.upload_video(ACCT, str(path), v["ad_name"])
            print(f"  {v['key']} uploaded video {vid}")
        vd = {"video_id": vid, "title": HEADLINE, "message": BODY,
              "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
        thumb = g.get_video_thumbnail(vid)
        if thumb:
            vd["image_url"] = thumb
        spec = {"page_id": PAGE_ID, "video_data": vd}
        if ig_ok:
            spec["instagram_user_id"] = ig_id
        try:
            creative[v["key"]] = g.create_adcreative(ACCT, name=v["ad_name"],
                                                     object_story_spec=spec, url_tags=UTM)["id"]
        except Exception as e:  # noqa: BLE001
            if not ig_ok:
                raise
            print(f"  IG id rejected ({str(e)[:90]}) — retrying page-backed")
            ig_ok = False
            spec.pop("instagram_user_id", None)
            creative[v["key"]] = g.create_adcreative(ACCT, name=v["ad_name"],
                                                     object_story_spec=spec, url_tags=UTM)["id"]
        print(f"  {v['key']} creative {creative[v['key']]} (IG {'set' if ig_ok else 'page-backed'})")

    print("== campaigns / ad sets / ads ==")
    have_c = existing(g, "campaigns")
    n_ads = 0
    for lvl in geo_levels:
        for aud in AUDIENCES:
            cname = f"US West | {lvl['label']} | {aud['name']}"
            cid = have_c.get(cname) or g.create_campaign(
                ACCT, name=cname, objective="OUTCOME_SALES", buying_type="AUCTION",
                status=STATUS, special_ad_categories=[],
                is_adset_budget_sharing_enabled=False)["id"]
            print(f"  campaign {cid}  {cname}")
            time.sleep(3)
            have_as = {r["name"]: r["id"] for r in g._get_all(f"{cid}/adsets", {"fields": "id,name"})}
            for v in VIDEOS:
                tgt = {"age_min": 35, "age_max": 65, "geo_locations": lvl["geo"],
                       "locales": [20, 21, 22], "excluded_custom_audiences": EXCLUDE,
                       "targeting_automation": {"advantage_audience": 0}}
                if lvl["exclude_geo"]:
                    tgt["excluded_geo_locations"] = lvl["exclude_geo"]
                if aud["flex"]:
                    tgt["flexible_spec"] = aud["flex"]
                asname = f"{aud['name']} | {lvl['adset_tag']} | {v['key']}"
                existed = asname in have_as
                asid = have_as.get(asname) or g.create_adset(
                    ACCT, campaign_id=cid, name=asname, daily_budget=DAILY,
                    bid_strategy="LOWEST_COST_WITHOUT_CAP",
                    optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                    promoted_object={"pixel_id": PIXEL_ID, "custom_event_type": "COMPLETE_REGISTRATION"},
                    targeting=tgt, status=STATUS)["id"]
                time.sleep(3)
                have_ads = ({r["name"] for r in g._get_all(f"{asid}/ads", {"fields": "name"})}
                            if existed else set())
                if v["ad_name"] not in have_ads:
                    adid = g.create_ad(ACCT, name=v["ad_name"], adset_id=asid,
                                       creative={"creative_id": creative[v["key"]]},
                                       status=STATUS)["id"]
                    n_ads += 1
                    time.sleep(3)
                    print(f"    adset {asid} {asname} -> ad {adid}")
                else:
                    print(f"    adset {asid} {asname} (ad exists)")

    print("== read-back of one ad set per geo level ==")
    for lvl in geo_levels:
        cname = f"US West | {lvl['label']} | Broad"
        cid = existing(g, "campaigns")[cname]
        a = g._get_all(f"{cid}/adsets", {"fields": "name,daily_budget,status,targeting"})[0]
        t = a["targeting"]
        print(f"  {a['name']}: budget {a['daily_budget']} status {a['status']}")
        print(f"    geo      {json.dumps(t.get('geo_locations'), ensure_ascii=False)}")
        print(f"    excl geo {json.dumps(t.get('excluded_geo_locations'), ensure_ascii=False)}")
        print(f"    excl aud {[x.get('id') for x in t.get('excluded_custom_audiences', [])]}")
    print(f"DONE — {n_ads} new ads, all {STATUS}")


if __name__ == "__main__":
    main()
