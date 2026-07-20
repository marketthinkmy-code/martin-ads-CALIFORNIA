"""Read-only: dump the reusable creative_id (+ object_story_id) for a list of ad IDs.

Why: the MCP has no ad->creative lookup, but to copy a proven ad into a new ad set we
need its creative_id (reusable within the same account). Env: AD_IDS = comma-separated.
"""
from __future__ import annotations

import json
import os

from adbot.commands import graph_client
from adbot.settings import load_settings


def main() -> None:
    ad_ids = [x.strip() for x in os.environ.get("AD_IDS", "").split(",") if x.strip()]
    if not ad_ids:
        raise SystemExit("Set AD_IDS=id1,id2,...")
    s = load_settings()
    g = graph_client(s)
    for aid in ad_ids:
        obj = g.get_object(aid, "name,creative{id,object_story_id,effective_object_story_id,video_id}")
        cr = obj.get("creative") or {}
        print(json.dumps({"ad_id": aid, "name": obj.get("name"),
                          "creative_id": cr.get("id"),
                          "object_story_id": cr.get("object_story_id") or cr.get("effective_object_story_id"),
                          "video_id": cr.get("video_id")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
