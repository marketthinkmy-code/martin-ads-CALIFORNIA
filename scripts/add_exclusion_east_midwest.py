"""Add the paid/registrant exclusion audience to the East+Midwest 1-3-1 ad sets.

Read-modify-write: GET each ad set's FULL targeting, append the audience to
excluded_custom_audiences, and POST it back. Never builds targeting from scratch — that would
silently drop the interest/behaviour/geo spec. Idempotent: skips ad sets that already exclude it.
"""
from __future__ import annotations

import json

from adbot.commands import graph_client
from adbot.logging import final_summary, get_logger
from adbot.settings import load_settings

EXCLUDE_ID = "120254451454000558"     # [美東美中 US] 15days complete registration
ADSETS = {
    "broad": "120254451454690558",
    "FR": "120254451455190558",
    "PE": "120254451455640558",
}


def main() -> None:
    log = get_logger()
    g = graph_client(load_settings())

    changed = skipped = 0
    for label, adset_id in ADSETS.items():
        cur = g.get_object(adset_id, "id,name,targeting")
        targeting = cur.get("targeting") or {}
        existing = list(targeting.get("excluded_custom_audiences") or [])
        if any(str(a.get("id")) == EXCLUDE_ID for a in existing):
            log.info("[%s] already excludes %s — skipping", label, EXCLUDE_ID)
            skipped += 1
            continue

        existing.append({"id": EXCLUDE_ID})
        targeting["excluded_custom_audiences"] = existing
        g._request("POST", adset_id, data={"targeting": json.dumps(targeting)})
        log.info("[%s] %s -> excluded_custom_audiences now %d entry(ies)",
                 label, adset_id, len(existing))
        changed += 1

    final_summary(log, f"Exclusion {EXCLUDE_ID} applied: {changed} ad set(s) updated, "
                       f"{skipped} already had it.")


if __name__ == "__main__":
    main()
