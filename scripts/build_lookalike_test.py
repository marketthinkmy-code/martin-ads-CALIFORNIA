"""One-off: build the Paid-List Lookalike TEST campaign.

Operator request: run the 1% / 1-2% / 2-3% / 3-4% / 4-5% US lookalikes (built off the
current Paid Student List) using the TOP-3 lifetime-converting ads as the creatives.

Structure: 1 CBO campaign (OUTCOME_SALES, RM150/day) + 5 ad sets — one per lookalike band —
each reusing the 3 proven creatives (creative_id is account-scoped + reusable). 15 ads total.
Geo = CA/WA/OR/NV states; the 3 paid/registrant audiences are excluded so the lookalikes don't
re-serve existing students. Advantage audience OFF so delivery stays inside the lookalike seed.
Idempotent via state. ACTIVE.
"""
from __future__ import annotations

from adbot import state
from adbot.commands import graph_client
from adbot.logging import final_summary, get_logger
from adbot.settings import load_settings

US_ACCT = "act_1629566827721449"
PIXEL_ID = "1921735088376759"
STATE_KEY = "entities_lookalike_test"
DAILY_CENTS = 15000  # RM150.00/day CBO across the 5 bands
STATUS = "ACTIVE"

GEO = {"regions": [{"key": "3847"}, {"key": "3871"}, {"key": "3880"}, {"key": "3890"}],
       "location_types": ["home", "recent"]}
# paid students + registrants — exclude so lookalikes don't re-serve people we already have
EXCLUDE = [{"id": "120236056842490259"}, {"id": "120240867576290259"}, {"id": "120243775674560259"}]

# the 1%..5% US lookalikes built off the current Paid Student List
BANDS = [
    {"key": "1pct",   "name": "Lookalike US 1%",     "lal": "120247871986410259"},
    {"key": "1_2pct", "name": "Lookalike US 1-2%",   "lal": "120247871986780259"},
    {"key": "2_3pct", "name": "Lookalike US 2-3%",   "lal": "120247871987070259"},
    {"key": "3_4pct", "name": "Lookalike US 3-4%",   "lal": "120247871987160259"},
    {"key": "4_5pct", "name": "Lookalike US 4-5%",   "lal": "120247871987420259"},
]

# top-3 lifetime converters (lifetime paid sales, from the paid-by-ad report) — reused by creative_id
CREATIVES = [
    {"key": "v1_huaren", "ad_name": "Video 1：华人孩子在美国很难长高", "creative_id": "1652829435631362"},
    {"key": "v5_lin",    "ad_name": "MAR Video 5：林書豪story",       "creative_id": "954839630290074"},
    {"key": "v4_chifan", "ad_name": "Video 4：吃饭喝水，咬咬吞",       "creative_id": "1034773655962494"},
]


def targeting_for(lal_id: str) -> dict:
    return {
        "age_min": 25, "age_max": 65, "geo_locations": GEO, "locales": [20, 21, 22],
        "custom_audiences": [{"id": lal_id}],
        "excluded_custom_audiences": EXCLUDE,
        "targeting_automation": {"advantage_audience": 0},
    }


def main() -> None:
    log = get_logger()
    s = load_settings()
    g = graph_client(s)

    st = state.load(STATE_KEY) or {}
    campaign_id = st.get("campaign_id")
    adsets = dict(st.get("adsets", {}))   # band key -> adset_id
    ads = dict(st.get("ads", {}))         # "band:creative" -> ad_id

    def persist():
        state.save(STATE_KEY, {"campaign_id": campaign_id, "adsets": adsets, "ads": ads})

    if not campaign_id:
        campaign_id = g.create_campaign(
            US_ACCT, name="US | Paid-List Lookalike TEST 1-5% (top-3 converters)",
            objective="OUTCOME_SALES", buying_type="AUCTION", status=STATUS,
            special_ad_categories=[], daily_budget=DAILY_CENTS,
            bid_strategy="LOWEST_COST_WITHOUT_CAP")["id"]
        persist()
        log.info("created campaign %s", campaign_id)

    summary = []
    for band in BANDS:
        bk = band["key"]
        if bk not in adsets:
            adsets[bk] = g.create_adset(
                US_ACCT, campaign_id=campaign_id, name=band["name"],
                optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                promoted_object={"pixel_id": PIXEL_ID, "custom_event_type": "COMPLETE_REGISTRATION"},
                targeting=targeting_for(band["lal"]), status=STATUS)["id"]
            persist()
            log.info("[%s] created ad set %s", bk, adsets[bk])
        for c in CREATIVES:
            adkey = f"{bk}:{c['key']}"
            if adkey in ads:
                continue
            ad = g.create_ad(US_ACCT, name=c["ad_name"], adset_id=adsets[bk],
                             creative={"creative_id": c["creative_id"]}, status=STATUS)
            ads[adkey] = ad["id"]
            persist()
            summary.append(f"  {adkey} -> ad {ad['id']}")
            log.info("[%s] built %s -> ad %s", bk, c["key"], ad["id"])

    log.info("=" * 60)
    for line in summary:
        log.info(line)
    final_summary(log, f"Lookalike TEST built ({STATUS}, CBO RM150/day): campaign {campaign_id}, "
                       f"{len(adsets)} bands x 3 creatives = {len(ads)} ads.")


if __name__ == "__main__":
    main()
