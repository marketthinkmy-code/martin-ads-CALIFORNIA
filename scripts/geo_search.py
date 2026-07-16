"""Read-only: resolve US state names to Meta ad-geo REGION KEYS (for geo_locations.regions).

Meta targets states via region keys (e.g. {"key":"3847"} = California), not names. This
hits the adgeolocation search endpoint — the same source Ads Manager's location box uses —
so config can carry verified keys instead of guessed ones.

Env: STATES = pipe-separated names ("California|Washington|Oregon|Nevada"). Defaults to those.
"""
from __future__ import annotations

import json
import os

from adbot.commands import graph_client
from adbot.settings import load_settings

DEFAULT = "California|Washington|Oregon|Nevada"


def main() -> None:
    states = [x.strip() for x in os.environ.get("STATES", DEFAULT).split("|") if x.strip()]
    s = load_settings()
    g = graph_client(s)
    for q in states:
        res = g._request("GET", "search", params={
            "type": "adgeolocation", "location_types": json.dumps(["region"]),
            "q": q, "country_code": "US", "limit": 5})
        rows = [{"key": r.get("key"), "name": r.get("name"),
                 "country": r.get("country_code"), "type": r.get("type")}
                for r in res.get("data", [])]
        print(f"=== {q} ===")
        print(json.dumps(rows, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
