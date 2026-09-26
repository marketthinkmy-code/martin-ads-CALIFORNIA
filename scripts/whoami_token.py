"""Read-only: ask Meta which system user META_SYSTEM_USER_TOKEN actually belongs to.

The operator has three system users in Business Settings and needs to grant the NEW ad
account to the right one. Guessing by name is a wasted round trip, so this prints the
token's own id/name plus the businesses and ad accounts it can already see.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.logging import final_summary, get_logger
from adbot.settings import load_settings

NEW_ACCT = "act_2022836788419850"
EM_ACCT = "act_921653460987535"


def main() -> None:
    log = get_logger()
    g = graph_client(load_settings())

    me = g._request("GET", "me", params={"fields": "id,name"})
    log.info("TOKEN IDENTITY: id=%s name=%s", me.get("id"), me.get("name"))

    try:
        biz = g._request("GET", "me/businesses", params={"fields": "id,name", "limit": 50})
        for b in biz.get("data", []):
            log.info("  business %s  %s", b.get("id"), b.get("name"))
    except Exception as e:  # noqa: BLE001 - diagnostic only
        log.info("  businesses unreadable: %s", e)

    for acct in (NEW_ACCT, EM_ACCT):
        try:
            r = g.get_object(acct, "id,name,account_status")
            log.info("  ✅ CAN SEE %s -> %s (status %s)", acct, r.get("name"), r.get("account_status"))
        except Exception as e:  # noqa: BLE001 - diagnostic only
            log.info("  ❌ CANNOT SEE %s -> %s", acct, e)

    final_summary(log, f"token is system user {me.get('id')} ({me.get('name')})")


if __name__ == "__main__":
    main()
