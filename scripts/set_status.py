"""Set the status of named campaigns / ad sets / ads (operator-approved changes only).

Env: IDS    = comma-separated object ids
     STATUS = ACTIVE | PAUSED
Each object is read back after the write so the log shows the live status.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_west_ab_nov as west  # noqa: E402  (throttle-tolerant wrapper)

from adbot.commands import graph_client  # noqa: E402
from adbot.settings import load_settings  # noqa: E402


def main() -> None:
    status = os.environ["STATUS"].strip().upper()
    if status not in {"ACTIVE", "PAUSED"}:
        raise SystemExit(f"STATUS must be ACTIVE or PAUSED, got {status}")
    ids = [x.strip() for x in os.environ["IDS"].split(",") if x.strip()]
    g = west.throttle_tolerant(graph_client(load_settings()))
    for oid in ids:
        g._request("POST", oid, data={"status": status})
        time.sleep(2)
        r = g._request("GET", oid, params={"fields": "name,status,effective_status"})
        print(f"{oid}  {r.get('name')}  status={r.get('status')}  effective={r.get('effective_status')}",
              flush=True)


if __name__ == "__main__":
    main()
