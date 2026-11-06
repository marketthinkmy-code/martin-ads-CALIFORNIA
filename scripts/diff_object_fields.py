"""Read-only: dump every readable field of some ad sets / ads / creatives and show the diff.

Used to find the API fields behind settings the operator sets by hand in Ads Manager
(e.g. "Strategy type: Get conversions from all audiences", the WhatsApp number in the ad
identity): compare an object the operator edited with one the API built and nobody touched.
Every documented field of the object type is requested; fields the API doesn't know are
skipped, so only real values are compared.

Env: IDS  = pipe-separated "label=id" (e.g. "edited=1201...|fresh=1202...").
     TYPE = adset | ad | creative (all IDS must be that type).
"""
from __future__ import annotations

import json
import os

from adbot.commands import graph_client
from adbot.settings import load_settings

FIELDS = {
    "adset": """account_id adset_schedule asset_feed_id attribution_spec automatic_manual_state
        bid_adjustments bid_amount bid_constraints bid_info bid_strategy billing_event
        brand_safety_config budget_remaining budget_schedule_specs campaign_active_time
        campaign_attribution campaign_id configured_status created_time creative_sequence
        daily_budget daily_min_spend_target daily_spend_cap destination_type dsa_beneficiary
        dsa_payor effective_status end_time existing_customer_budget_percentage
        frequency_control_specs full_funnel_exploration_mode instagram_user_id
        is_ba_skip_delayed_eligible is_budget_schedule_enabled is_dynamic_creative
        is_incremental_attribution_enabled issues_info learning_stage_info lifetime_budget
        lifetime_imps lifetime_min_spend_target lifetime_spend_cap max_budget_spend_percentage
        min_budget_spend_percentage multi_optimization_goal_weight name optimization_goal
        optimization_sub_event pacing_type placement_soft_opt_out promoted_object
        recurring_budget_semantics regional_regulated_categories
        regional_regulation_identities review_feedback rf_prediction_id source_adset_id
        start_time status targeting_optimization_types time_based_ad_rotation_id_blocks
        time_based_ad_rotation_intervals trending_topics_spec value_rule_set_id
        value_rules_applied targeting""".split(),
    "ad": """account_id ad_active_time ad_review_feedback ad_schedule_end_time
        ad_schedule_start_time adset_id bid_amount campaign_id configured_status
        conversion_domain conversion_specs created_time creative creative_asset_groups_spec
        display_sequence effective_status engagement_audience failed_delivery_checks
        issues_info last_updated_by_app_id meta_reward_adgroup_status name
        preview_shareable_link source_ad_id status tracking_specs updated_time""".split(),
    "creative": """account_id actor_id applink_treatment asset_feed_spec authorization_category
        body branded_content branded_content_sponsor_page_id bundle_folder_id call_to_action
        call_to_action_type categorization_criteria category_media_source contextual_multi_ads
        creative_sourcing_spec degrees_of_freedom_spec destination_set_id dynamic_ad_voice
        effective_authorization_category effective_instagram_media_id
        effective_object_story_id enable_direct_install enable_launch_instant_app
        facebook_branded_content image_crops image_hash image_url instagram_branded_content
        instagram_permalink_url instagram_user_id interactive_components_spec
        link_deep_link_url link_destination_display_url link_og_id link_url
        messenger_sponsored_message name object_id object_store_url object_story_id
        object_story_spec object_type object_url page_welcome_message
        photo_album_source_object_story_id place_page_set_id platform_customizations
        playable_asset_id portrait_customizations product_data product_set_id
        recommender_settings regional_regulation_disclaimer_spec source_facebook_post_id
        source_instagram_media_id status template_url template_url_spec thumbnail_id
        thumbnail_url title url_tags use_page_actor_override video_id""".split(),
}

SKIP = {"targeting", "adlabels", "recommendations", "insights", "copies", "previews",
        "ad_studies", "keyword_stats", "leads", "targetingsentencelines", "adrules_governed",
        "delivery_estimate", "asyncadrequests", "activities", "ads", "adsets", "adcreatives",
        "content_delivery_report", "message_delivery_estimate", "targeting_sentence_lines"}


def dump(g, oid, typ):
    names = FIELDS[typ]
    out = {"_type": typ}
    for i in range(0, len(names), 25):
        chunk = names[i:i + 25]
        try:
            out.update(g._request("GET", oid, params={"fields": ",".join(chunk)}))
        except Exception:  # noqa: BLE001 — some fields are not readable on every object
            for n in chunk:
                try:
                    out.update(g._request("GET", oid, params={"fields": n}))
                except Exception:  # noqa: BLE001 — not a field on this object/version
                    pass
    return out


def flatten(v, prefix=""):
    """Nested dict/list -> {"a.b[0].c": leaf} so long objects diff by exact sub-path."""
    if isinstance(v, dict):
        out = {}
        for k, x in v.items():
            out.update(flatten(x, f"{prefix}.{k}" if prefix else k))
        return out
    if isinstance(v, list):
        out = {}
        for i, x in enumerate(v):
            out.update(flatten(x, f"{prefix}[{i}]"))
        return out or {prefix: []}
    return {prefix: v}


NOISE = ("thumbnail", "image_url", "image_hash", "video_id", "effective_", "permalink",
         "account_id", "created_time", "updated_time", "_nc_", "url_tags")


def main() -> None:
    g = graph_client(load_settings())
    pairs = [x.split("=", 1) for x in os.environ["IDS"].split("|") if "=" in x]
    typ = os.environ.get("TYPE", "adset")
    data = {label: dump(g, oid, typ) for label, oid in pairs}
    for label, d in data.items():
        print(f"===== {label} ({d.get('id')}, {d.get('_type')}) =====")
        print(json.dumps(d, ensure_ascii=False, sort_keys=True)[:3000])
    labels = list(data)
    flat = {l: flatten(d) for l, d in data.items()}
    print("===== SUB-FIELDS THAT DIFFER (noise filtered) =====")
    for k in sorted(set().union(*[set(f) for f in flat.values()])):
        if any(n in k for n in NOISE):
            continue
        vals = [json.dumps(flat[l].get(k), ensure_ascii=False) for l in labels]
        if len(set(vals)) > 1:
            print(f"- {k}: " + " | ".join(f"{l}={v[:160]}" for l, v in zip(labels, vals)))
    keys = sorted(set().union(*[set(d) for d in data.values()]))
    print("===== FIELDS THAT DIFFER =====")
    for k in keys:
        vals = [json.dumps(data[l].get(k), ensure_ascii=False, sort_keys=True) for l in labels]
        if len(set(vals)) > 1 and k not in {"id", "name", "created_time", "updated_time"}:
            print(f"- {k}:")
            for l, v in zip(labels, vals):
                print(f"    {l}: {v[:300]}")


if __name__ == "__main__":
    main()
