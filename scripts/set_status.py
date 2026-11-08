"""Set the status or daily budget of named campaigns / ad sets / ads (operator-approved only).

Env: IDS    = comma-separated object ids
     STATUS = ACTIVE | PAUSED (optional if DAILY_BUDGET is set)
     DAILY_BUDGET = new daily budget in the account currency's minor unit, e.g. 6500 = RM65
Each object is read back after the write so the log shows the live status and budget.
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
    status = os.environ.get("STATUS", "").strip().upper()
    budget = os.environ.get("DAILY_BUDGET", "").strip()
    if status and status not in {"ACTIVE", "PAUSED"}:
        raise SystemExit(f"STATUS must be ACTIVE or PAUSED, got {status}")
    if budget and not budget.isdigit():
        raise SystemExit(f"DAILY_BUDGET must be an integer in minor units, got {budget}")
    if not status and not budget:
        raise SystemExit("nothing to change: set STATUS and/or DAILY_BUDGET")
    data = {**({"status": status} if status else {}), **({"daily_budget": budget} if budget else {})}
    ids = [x.strip() for x in os.environ["IDS"].split(",") if x.strip()]
    g = west.throttle_tolerant(graph_client(load_settings()))
    for oid in ids:
        g._request("POST", oid, data=data)
        time.sleep(2)
        fields = "name,status,effective_status" + (",daily_budget" if budget else "")
        r = g._request("GET", oid, params={"fields": fields})
        print(f"{oid}  {r.get('name')}  status={r.get('status')}  effective={r.get('effective_status')}"
              + (f"  daily_budget={r.get('daily_budget')}" if budget else ""), flush=True)


if __name__ == "__main__":
    main()
