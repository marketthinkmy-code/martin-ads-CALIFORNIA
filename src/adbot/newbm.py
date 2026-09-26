"""Graph client for the NEW business's ad account (act_2022836788419850).

That account lives under a different business than everything else in this repo, and the
system user whose token is META_SYSTEM_USER_TOKEN has no access to it. Rather than move the
whole repo onto a new token — which would break the East+Midwest and California automations —
new-account work uses its own token from META_NEW_BM_TOKEN and leaves the rest untouched.

META_NEW_BM_APP_SECRET is optional: appsecret_proof is only sent when a secret is supplied,
and the new token may come from a different app than META_APP_SECRET belongs to, in which case
sending the wrong proof would fail every call.
"""
from __future__ import annotations

import os

from .clients.graph import GraphClient
from .logging import register_secret

NEW_ACCT = "act_2022836788419850"


def new_bm_client() -> GraphClient:
    token = os.environ.get("META_NEW_BM_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "META_NEW_BM_TOKEN is not set. Generate a token for the system user that has "
            f"access to {NEW_ACCT} and store it as a repository secret."
        )
    secret = os.environ.get("META_NEW_BM_APP_SECRET", "").strip()
    register_secret(token)
    register_secret(secret)
    return GraphClient(token, secret)
