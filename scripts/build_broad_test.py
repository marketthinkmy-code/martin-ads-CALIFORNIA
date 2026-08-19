"""One-off: build a BROAD (Advantage+ audience) TEST campaign, RM100/day.

Operator diagnosis: high CPL came from a broken landing-page date (15-19), not audience.
Separately, CPM is high because every campaign uses narrow interest stacks. This campaign
attacks CPM directly: NO interests — geo (CA/WA/OR/NV) + age only, Advantage Audience ON,
reusing the top-3 lifetime-converting creatives. 1 CBO campaign + 1 broad ad set + 3 ads.
Paid students + registrants excluded. ACTIVE. Idempotent via state.
"""
from __future__ import annotations

from adbot import state
from adbot.commands import graph_client
from adbot.logging import final_summary, get_logger
from adbot.settings import load_settings

US_ACCT = "act_1629566827721449"
PIXEL_ID = "1921735088376759"
STATE_KEY = "entities_broad_test"
DAILY_CENTS = 10000  # RM100.00/day CBO
STATUS = "ACTIVE"

GEO = {"regions": [{"key": "3847"}, {"key": "3871"}, {"key": "3880"}, {"key": "3890"}],
       "location_types": ["home", "recent"]}
EXCLUDE = [{"id": "120236056842490259"}, {"id": "120240867576290259"}, {"id": "120243775674560259"}]

# broad: geo + age only, NO interests, Advantage Audience ON — lets Meta widen the pool + drop CPM
TARGETING = {
    "age_min": 25, "age_max": 65, "geo_locations": GEO, "locales": [20, 21, 22],
    "excluded_custom_audiences": EXCLUDE,
    "targeting_automation": {"advantage_audience": 1},
}

# top-3 lifetime converters — reused by creative_id (account-scoped, reusable)
CREATIVES = [
    {"key": "v1_huaren", "ad_name": "Video 1：华人孩子在美国很难长高", "creative_id": "1652829435631362"},
    {"key": "v5_lin",    "ad_name": "MAR Video 5：林書豪story",       "creative_id": "954839630290074"},
    {"key": "v4_chifan", "ad_name": "Video 4：吃饭喝水，咬咬吞",       "creative_id": "1034773655962494"},
]


def main() -> None:
    log = get_logger()
    s = load_settings()
    g = graph_client(s)

    st = state.load(STATE_KEY) or {}
    campaign_id = st.get("campaign_id")
    adset_id = st.get("adset_id")
    ads = dict(st.get("ads", {}))

    def persist():
        state.save(STATE_KEY, {"campaign_id": campaign_id, "adset_id": adset_id, "ads": ads})

    if not campaign_id:
        campaign_id = g.create_campaign(
            US_ACCT, name="US | BROAD (Advantage+ audience) TEST | top-3 creatives",
            objective="OUTCOME_SALES", buying_type="AUCTION", status=STATUS,
            special_ad_categories=[], daily_budget=DAILY_CENTS,
            bid_strategy="LOWEST_COST_WITHOUT_CAP")["id"]
        persist()
        log.info("created campaign %s", campaign_id)

    if not adset_id:
        adset_id = g.create_adset(
            US_ACCT, campaign_id=campaign_id, name="Broad · CA/WA/OR/NV · 25-65 · Advantage+",
            optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
            promoted_object={"pixel_id": PIXEL_ID, "custom_event_type": "COMPLETE_REGISTRATION"},
            targeting=TARGETING, status=STATUS)["id"]
        persist()
        log.info("created ad set %s", adset_id)

    summary = []
    for c in CREATIVES:
        if c["key"] in ads:
            continue
        ad = g.create_ad(US_ACCT, name=c["ad_name"], adset_id=adset_id,
                         creative={"creative_id": c["creative_id"]}, status=STATUS)
        ads[c["key"]] = ad["id"]
        persist()
        summary.append(f"  {c['key']} -> ad {ad['id']}")
        log.info("built %s -> ad %s", c["key"], ad["id"])

    log.info("=" * 60)
    for line in summary:
        log.info(line)
    final_summary(log, f"Broad TEST built ({STATUS}, CBO RM100/day): campaign {campaign_id}, "
                       f"ad set {adset_id}, {len(ads)} ads.")


if __name__ == "__main__":
    main()
