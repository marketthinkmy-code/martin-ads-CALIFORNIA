"""Read-only: resolve US state names to Meta ad-geo REGION KEYS (for geo_locations.regions).

Meta targets states via region keys (e.g. {"key":"3847"} = California), not names. This
hits the adgeolocation search endpoint — the same source Ads Manager's location box uses —
so config can carry verified keys instead of guessed ones.

Env: STATES = pipe-separated names ("California|Washington|Oregon|Nevada"). Defaults to those.
    QUERIES = optional pipe-separated "type:name:country" lookups for any location type, e.g.
              "city:Flushing:US|neighborhood:Bayside:US|region:Ontario:CA". When set, STATES is
              ignored. Types: country, region, city, subcity, neighborhood, zip.
"""
from __future__ import annotations

import json
import os

from adbot.commands import graph_client
from adbot.settings import load_settings

DEFAULT = "California|Washington|Oregon|Nevada"


def search_any(g, spec: str) -> None:
    typ, q, cc = (spec.split(":") + ["", ""])[:3]
    params = {"type": "adgeolocation", "location_types": json.dumps([typ]), "q": q, "limit": 8}
    if cc:
        params["country_code"] = cc
    res = g._request("GET", "search", params=params)
    rows = [{k: r.get(k) for k in ("key", "name", "type", "region", "region_id", "country_code",
                                    "primary_city", "primary_city_id")}
            for r in res.get("data", [])]
    print(f"=== {spec} ===")
    print(json.dumps(rows, indent=1, ensure_ascii=False))


def main() -> None:
    queries = [x.strip() for x in os.environ.get("QUERIES", "").split("|") if x.strip()]
    if queries:
        g = graph_client(load_settings())
        for spec in queries:
            search_any(g, spec)
        return
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
