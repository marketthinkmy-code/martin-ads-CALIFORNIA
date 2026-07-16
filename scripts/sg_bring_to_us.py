"""Read-only: locate the SG top-performing ads (minus milk/bread creatives) inside
the SG ad account and report the fields needed to re-run them on the 加州/US account.

Why: a creative_id / video_id is ad-account-scoped and can't be reused across accounts.
But an `object_story_id` (pageID_postID) is owned by the PAGE — and the US account can
already reference page 341825319024143 posts (it has a live creative doing so). So for
each SG winner we surface its object_story_id + the page it lives on; any post on a page
the US account can post as is directly reusable as an existing-post US ad.

MILK/BREAD creatives are intentionally EXCLUDED (operator: not suitable for US).
Read-only — no writes.
"""
from __future__ import annotations

import json
import re

from adbot.clients.graph import GraphClient
from adbot.settings import load_settings

SG_ACCT = "act_1024930575770087"
US_PAGE = "341825319024143"   # the page the US account can already reference

# 10 keep-ads (milk/bread winners #2 #5 #10 #14 #15 dropped by the operator)
KEEP = [
    "Video 2 - 一个3～15岁正常健康的孩子",
    "Video: 孩子15岁以上还有机会长高吗?",
    "JAN Video 6: 如果你的孩子",
    "Hook 18: 13 141cm",
    "Extra Video 1 - 鼻子敏感",
    "MAR Video 5: 林書豪 story",
    "MAY Video Hook 1: 10 个孩子会有 8 个",
    "Video Hook 2: 运动但是没长高",
    "JAN Video 10: 马六甲",
    "见证 1: 短头发 Eunice Ngu",
]

TRAD2SIMP = str.maketrans({
    "麵": "面", "書": "书", "長": "长", "見": "见", "證": "证", "馬": "马",
    "頭": "头", "個": "个", "會": "会", "還": "还", "學": "学", "習": "习",
    "歲": "岁", "對": "对", "來": "来", "媽": "妈", "營": "营", "養": "养",
    "師": "师", "後": "后", "們": "们",
})
PUNCT = str.maketrans({
    "：": ":", "（": "(", "）": ")", "～": "~", "！": "!", "？": "?",
    "，": ",", "．": ".", "－": "-", "—": "-", "–": "-", "、": ",",
})


def norm(s: str) -> str:
    s = (s or "").strip().lower().translate(TRAD2SIMP).translate(PUNCT)
    return re.sub(r"\s+", "", s)


def longest_cjk(s: str) -> str:
    runs = re.findall(r"[一-鿿]+", (s or "").translate(TRAD2SIMP))
    return max(runs, key=len) if runs else ""


def main() -> None:
    s = load_settings()
    g = GraphClient(s.secrets.meta_token, "")

    ads = g._get_all(f"{SG_ACCT}/ads",
                     {"fields": "name,effective_status,creative{id,object_story_id,"
                                "effective_object_story_id,video_id,object_type,thumbnail_url}",
                      "limit": 500})
    print(f"SG account {SG_ACCT}: {len(ads)} ads pulled\n")
    idx = [(norm(a.get("name", "")), a) for a in ads]

    def report(a: dict) -> str:
        cr = a.get("creative") or {}
        osid = cr.get("object_story_id") or cr.get("effective_object_story_id") or ""
        page = osid.split("_")[0] if "_" in osid else "?"
        reusable = "✅ REUSABLE on US" if page == US_PAGE else f"⚠️ page {page} (verify US access)"
        return (f"      name={a.get('name','')!r}  status={a.get('effective_status')}\n"
                f"      object_story_id={osid or '(none)'}  video_id={cr.get('video_id','?')}  "
                f"type={cr.get('object_type','?')}\n"
                f"      thumbnail_url={cr.get('thumbnail_url','?')}\n      {reusable}")

    for i, top in enumerate(KEEP, 1):
        nt = norm(top)
        exact = [a for (na, a) in idx if na == nt]
        print(f"#{i:>2}  {top}")
        if exact:
            best = sorted(exact, key=lambda a: 0 if a.get("effective_status") == "ACTIVE" else 1)[0]
            print(report(best))
        else:
            core = longest_cjk(top)
            cand = [a for (na, a) in idx if core and norm(core) in na][:6]
            if cand:
                print(f"    (no exact match — {len(cand)} candidate(s) containing {core!r}):")
                for a in cand:
                    print(report(a))
            else:
                print("    ❌ not found in SG account")
        print()


if __name__ == "__main__":
    main()
