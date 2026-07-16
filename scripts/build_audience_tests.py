"""Build US audience-test campaigns — 1 campaign + 1 ad set + 3 ads each, ALL PAUSED.

Ported from martin-ads-SG (the proven playbook). Each campaign targets one
top-converting audience; the ad set's DETAILED TARGETING is CLONED LIVE from that
audience's canonical winning ad set anywhere in the portfolio (SG/MY/US) — keeping
the exact interest / behavior / family-status IDs, which are global. Cloning from a
live ad set is the ONLY safe source of detailed-targeting IDs: Meta ignores the
`name` field on write and silently accepts any existing ID, so a guessed ID lands
as a completely different audience (e.g. "Cosmetics" instead of "Early childhood
education" — the 2026-07-16 incident).

The spec is then forced to US geo (home+recent) + the four US exclusion audiences
and stripped of any account-scoped custom audiences.

  • CBO RM100/day per campaign · everything PAUSED (zero spend until review)
  • the SAME 3 成绩 social-proof creatives in every ad set — audience is the only variable
  • campaign name 'PNW | <audience> | 1-1-3' (prefix PNW, matching the operator's US test)
  • optional START_TIME env (ISO8601 with offset) schedules delivery

Idempotent: each audience has its own state_key, so a re-dispatch reuses recorded
campaign / ad set / ad IDs and is a no-op.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from adbot.build_1_1_10 import build
from adbot.caption_source import load_from_notion
from adbot.commands import drive_client, graph_client, notion_client
from adbot.drive_sync import download_assets, load_units
from adbot.logging import final_summary, get_logger
from adbot.settings import load_settings

PREFIX = "PNW"
DAILY_MYR = 100
START_TIME = os.environ.get("START_TIME", "").strip() or None

# Default geo = the 4 operator states (verified Meta region keys via scripts/geo_search.py):
# 3847 California · 3890 Washington · 3880 Oregon · 3871 Nevada.
US_GEO = {"countries": ["US"], "location_types": ["home", "recent"],
          "regions": [{"key": "3847"}, {"key": "3890"}, {"key": "3880"}, {"key": "3871"}]}
US_EXCL = [{"id": "120236056842490259"},   # US 15days complete registration
           {"id": "120220335292090259"},   # 60days complete registration
           {"id": "120240867576290259"},   # MARTIN US PAID CUSTOMER - APR 13
           {"id": "120243775674560259"}]   # US PAID STUDENTS MAY 2026

# The 3 constant 成绩 creatives — picked from the GRADES US "F" Drive subfolder by
# content id (already uploaded once by build-us-grades, so media_cache makes this free).
F_SUBFOLDER_ID = "1eBVmz7nOl6FhPr8a2vbD69rVwe4PWKrF"
CREATIVE_IDS = ["us_f1_parents_report", "us_f2_april_compare", "us_f5_shortterm_two_kids"]

# (display label, canonical winning ad-set NAME to clone the targeting from — the
# portfolio-wide top converters per the Paid Student List join)
AUDIENCES: List[Dict[str, str]] = [
    {"label": "Parents 3-17 + Engaged",   "clone": "Advantage+ Parents + Engaged"},
    {"label": "Family and Relationships", "clone": "Interest: Family and Relationships"},
    {"label": "Housewife",                "clone": "Housewife"},
    {"label": "Food & Drink + Milk",      "clone": "Interest: Food and Drink + Milk"},
    {"label": "Education-Tuition",        "clone": "Education"},
]

DETAIL_KEYS = ["interests", "behaviors", "life_events", "family_statuses", "industries",
               "income", "education_statuses", "work_positions", "work_employers",
               "relationship_statuses", "user_adclusters", "moms"]


def _slug(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def pull_adsets(g) -> List[dict]:
    """Every ad set (name + targeting) across every account this token can see."""
    log = get_logger()
    accts = g._get_all("me/adaccounts", {"fields": "account_id", "limit": 200})
    out: List[dict] = []
    for a in accts:
        path = f"act_{a['account_id']}"
        try:
            out += g._get_all(f"{path}/adsets",
                              {"fields": "name,effective_status,targeting", "limit": 500})
        except Exception as e:                       # noqa: BLE001
            log.warning("adsets pull failed for %s: %s", path, e)
    return out


def _richness(t: dict) -> int:
    if not isinstance(t, dict):
        return 0

    def count(spec: dict) -> int:
        return sum(len(spec.get(k) or []) for k in DETAIL_KEYS)

    n = count(t)
    for grp in (t.get("flexible_spec") or []):
        n += count(grp)
    return n


def clone_targeting(adsets: List[dict], name: str) -> Tuple[Optional[dict], Optional[str]]:
    """Rebuild a clean US-valid targeting spec from the richest ad set called `name`.

    Keeps only detailed targeting (flexible_spec interest/behavior/… IDs — global)
    plus age / gender / advantage_audience; forces US geo + the four US exclusions;
    drops any account-scoped custom audiences. Returns (spec, source_name) or (None, None).
    """
    key = name.strip().lower()
    matches = [a for a in adsets if (a.get("name") or "").strip().lower() == key]
    if not matches:  # fall back to substring
        matches = [a for a in adsets if key in (a.get("name") or "").strip().lower()]
    if not matches:
        return None, None

    best = max(matches, key=lambda a: _richness(a.get("targeting") or {}))
    t = best.get("targeting") or {}

    adv_raw = (t.get("targeting_automation") or {}).get("advantage_audience")
    adv = 1 if adv_raw is None else int(adv_raw)
    age_min = int(t.get("age_min") or 25)
    age_max = int(t.get("age_max") or 65)
    if adv == 1 and age_min > 25:   # Meta rejects a hard age_min > 25 when Advantage+ audience is on
        age_min = 25

    spec: Dict[str, Any] = {
        "geo_locations": US_GEO,
        "age_min": age_min,
        "age_max": age_max,
        "targeting_automation": {"advantage_audience": adv},
        "excluded_custom_audiences": US_EXCL,
        "locales": [1004],
    }
    genders = t.get("genders")
    if genders:
        spec["genders"] = genders
    fs = t.get("flexible_spec")
    if fs:
        spec["flexible_spec"] = fs
    else:
        legacy = {k: t[k] for k in DETAIL_KEYS if t.get(k)}
        if legacy:
            spec["flexible_spec"] = [legacy]
    return spec, best.get("name")


def main() -> None:
    log = get_logger()
    s = load_settings()
    g = graph_client(s)

    # per-request overrides (config stays broad for the normal builds)
    s.naming.prefix = PREFIX
    s.meta.budget.level = "CAMPAIGN"          # CBO
    s.meta.budget.daily_amount_myr = DAILY_MYR

    # 3 constant creative units from the F subfolder (media_cache dedupes the upload)
    drive = drive_client(s)
    s.drive.creatives_folder_id = F_SUBFOLDER_ID
    _, units = load_units(drive, s)
    units = [u for u in units if u.content_id in CREATIVE_IDS]
    missing = set(CREATIVE_IDS) - {u.content_id for u in units}
    if missing:
        raise SystemExit(f"F-subfolder is missing creatives {sorted(missing)} — check Drive access")
    captions = load_from_notion(notion_client(s), s, units)   # strict: hard error if a caption is missing
    download_assets(drive, units)
    log.info("units + captions ready for %d creatives", len(units))

    all_adsets = pull_adsets(g)
    log.info("pulled %d ad sets across accounts", len(all_adsets))

    summary: List[str] = []
    for aud in AUDIENCES:
        spec, src = clone_targeting(all_adsets, aud["clone"])
        if spec is None:
            log.error("!! no ad set named like %r to clone — SKIPPING %s", aud["clone"], aud["label"])
            summary.append(f"  SKIPPED  {aud['label']}  (no clone source for {aud['clone']!r})")
            continue

        detail = _richness({"flexible_spec": spec.get("flexible_spec", [])})
        log.info("── %s  ← cloned from %r  (age %s-%s · genders=%s · %d detail-targeting entries)",
                 aud["label"], src, spec["age_min"], spec["age_max"],
                 spec.get("genders", "all"), detail)

        ent = build(
            g, s, units=units, captions=captions, dry_run=False,
            label=f"{aud['label']} | 1-1-3",
            state_key="entities_us_audtest_" + _slug(aud["label"]),
            adset_name=f"{PREFIX} | {aud['label']} | AdSet",
            targeting_override=spec,
            start_time=START_TIME,
        )
        summary.append(f"  {aud['label']:26} campaign={ent['campaign_id']} "
                       f"adset={ent['adset_id']} ads={len(ent['ad_ids'])}")

    log.info("═" * 78)
    log.info("US audience-test build result (all PAUSED, CBO RM%d/day, start %s):",
             DAILY_MYR, START_TIME or "immediate-on-activate")
    for line in summary:
        log.info(line)
    final_summary(log, f"US audience tests built: {len([x for x in summary if 'campaign=' in x])}"
                       f"/{len(AUDIENCES)} campaigns (1-1-3 each, PAUSED). Review + activate in Ads Manager.")


if __name__ == "__main__":
    main()
