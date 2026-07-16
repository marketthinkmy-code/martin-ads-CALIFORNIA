"""Read-only: resolve Detailed Targeting keywords to REAL Meta targeting IDs.

Why this exists: the ads MCP has no targeting-search tool, and Meta silently ignores
the `name` field in a written spec — an invented ID that happens to exist lands as a
completely different audience (e.g. 6002839660079 turned out to be "Cosmetics", not
"Early childhood education"). This script queries the same Graph endpoints Ads
Manager's search box uses, so specs can be written with verified IDs only.

Env: QUERIES = pipe-separated keywords ("Early childhood education|Milk|Motherhood").
Also dumps the account's browsable family_statuses/demographics categories.
"""
from __future__ import annotations

import json
import os

from adbot.commands import graph_client
from adbot.settings import load_settings


def main() -> None:
    queries = [q.strip() for q in os.environ.get("QUERIES", "").split("|") if q.strip()]
    if not queries:
        raise SystemExit("Set QUERIES='kw1|kw2|...'")
    s = load_settings()
    g = graph_client(s)
    acct = s.meta.account_path

    for q in queries:
        res = g._request("GET", f"{acct}/targetingsearch", params={"q": q, "limit": 8})
        rows = [{"id": r.get("id"), "name": r.get("name"), "type": r.get("type"),
                 "path": " > ".join(r.get("path") or []),
                 "audience": r.get("audience_size_lower_bound")}
                for r in res.get("data", [])]
        print(f"=== {q} ===")
        print(json.dumps(rows, indent=1, ensure_ascii=False))

    # demographics (parents segments etc.) come from targetingbrowse, not search
    res = g._request("GET", f"{acct}/targetingbrowse", params={"limit_type": "demographics"})
    demo = [{"id": r.get("id"), "name": r.get("name"), "type": r.get("type"),
             "path": " > ".join(r.get("path") or [])} for r in res.get("data", [])]
    print("=== BROWSE demographics ===")
    print(json.dumps(demo, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
