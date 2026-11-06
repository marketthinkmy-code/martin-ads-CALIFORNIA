"""Read-only: dump every readable field of some ad sets / ads / creatives and show the diff.

Used to find the API fields behind settings the operator sets by hand in Ads Manager
(e.g. "Strategy type: Get conversions from all audiences", the WhatsApp number in the ad
identity): compare an object the operator edited with one the API built and nobody touched.
Field lists come from the Graph API's own metadata, so nothing is guessed.

Env: IDS = pipe-separated "label=id" (e.g. "edited=1201...|fresh=1202...").
"""
from __future__ import annotations

import json
import os

from adbot.commands import graph_client
from adbot.settings import load_settings

SKIP = {"targeting", "adlabels", "recommendations", "insights", "copies", "previews",
        "ad_studies", "keyword_stats", "leads", "targetingsentencelines", "adrules_governed",
        "delivery_estimate", "asyncadrequests", "activities", "ads", "adsets", "adcreatives",
        "content_delivery_report", "message_delivery_estimate", "targeting_sentence_lines"}


def dump(g, oid):
    meta = g._request("GET", oid, params={"metadata": 1})
    md = meta.get("metadata", {})
    names = [f["name"] for f in md.get("fields", []) if f["name"] not in SKIP]
    out = {"_type": md.get("type")}
    for i in range(0, len(names), 25):
        chunk = names[i:i + 25]
        try:
            out.update(g._request("GET", oid, params={"fields": ",".join(chunk)}))
        except Exception:  # noqa: BLE001 — some fields are not readable on every object
            for n in chunk:
                try:
                    out.update(g._request("GET", oid, params={"fields": n}))
                except Exception as e:  # noqa: BLE001
                    out[n] = f"!! {str(e)[:60]}"
    return out


def main() -> None:
    g = graph_client(load_settings())
    pairs = [x.split("=", 1) for x in os.environ["IDS"].split("|") if "=" in x]
    data = {label: dump(g, oid) for label, oid in pairs}
    for label, d in data.items():
        print(f"===== {label} ({d.get('id')}, {d.get('_type')}) =====")
        print(json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True)[:20000])
    labels = list(data)
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
