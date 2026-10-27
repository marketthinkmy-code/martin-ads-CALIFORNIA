"""Read-only: the US top-converting ads, with name variants merged and spend joined.

The plain paid-by-ad report counts by the raw UTM ad name, so ONE video shows up as several
rows ("Video 1：华人孩子在美国很难长高？", "Video 1: 华人孩子在美国很难长高", the 繁體 copy, the
"US East-Midwest | ..." copy) and its sales are split. This merges them under a canonical
creative key (traditional→simplified, punctuation and "Video N / Hook N / MAR" labels
stripped), splits sales by market (Canada campaigns live in the same tab and are excluded
from the US ranking), and joins lifetime spend + registrations from every US ad account so
each winner gets a real cost per sale.

Prints ad names and counts only — no customer data leaves the runner.
"""
from __future__ import annotations

import datetime as dt
import re
from collections import Counter, defaultdict

from opencc import OpenCC

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import load_settings

US_ACCOUNTS = {
    "California": "act_1629566827721449",
    "East+Midwest": "act_921653460987535",
}
_t2s = OpenCC("t2s").convert
_LABEL = re.compile(r"^(mar|apr|may|jun|jul|aug|sep|oct)?\s*"
                    r"(北美\s*hook|北美\s*h|short\s*video|single\s*image|video|hook|post|h)?\s*\d*\s*[:：\-]?\s*",
                    re.I)


def key(name: str) -> str:
    n = cpa.norm(name)
    if "|" in n:                      # "US East-Midwest | Video: X" -> "video: x"
        n = n.rsplit("|", 1)[1].strip()
    n = _t2s(n)
    n = _LABEL.sub("", n, count=1)
    n = re.sub(r"^加州", "", n)       # CA copy of the same video carried the state in its name
    n = re.sub(r"\s*20\d\d-\d\d-\d\d-[0-9a-f]{32}$", "", n)   # Meta auto-suffix on creative names
    return re.sub(r"[^0-9a-z一-鿿]", "", n)


def market(campaign: str) -> str:
    c = _t2s(cpa.norm(campaign))
    if any(t in c for t in ("温哥华", "vancouver", "bc-", "bc ", "canada", "加拿大")):
        return "Canada"
    if "east" in c:
        return "East+Midwest"
    if "pnw" in c:
        return "PNW"
    if "cal" in c or "加州" in c:
        return "California"
    return "Other"


def main() -> None:
    s = load_settings()
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    values = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab)
    sales, _, _ = cpa.parse_sales(values, s.cpa.price_myr)

    by_key = defaultdict(list)
    variants = defaultdict(Counter)
    unattributed = 0
    mk_total = Counter()
    for x in sales:
        mk_total[market(x.campaign)] += 1
        if not x.ad:
            unattributed += 1
            continue
        k = key(x.ad)
        by_key[k].append(x)
        variants[k][x.ad] += 1

    # lifetime spend + registrations per canonical key across US accounts
    g = graph_client(s)
    tok = result_action_type(s.meta.conversion_event)
    spend, regs, accts = defaultdict(float), defaultdict(float), defaultdict(set)
    for label, acct in US_ACCOUNTS.items():
        try:
            rows = g.account_insights(acct, level="ad", fields="ad_name,spend,actions",
                                      date_preset="maximum")
        except Exception as e:  # noqa: BLE001
            print(f"!! could not read {label} ({acct}): {e}")
            continue
        for r in rows:
            k = key(r.get("ad_name", ""))
            spend[k] += float(r.get("spend") or 0)
            regs[k] += float(extract_results(r.get("actions"), tok) or 0)
            accts[k].add(label)

    def win(rows, days):
        return sum(1 for r in rows if r.date and r.date > today - dt.timedelta(days=days))

    print(f"=== US TOP ADS · merged variants · today MYT={today} ===")
    print(f"Tab '{s.cpa.sales_tab}': {len(sales)} sales · {unattributed} with no ad name")
    print("Sales by market (whole tab): " + ", ".join(f"{m} {n}" for m, n in mk_total.most_common()))
    last_sale = max((x.date for x in sales if x.date), default=None)
    print(f"Most recent dated sale: {last_sale}\n")

    table = []
    for k, rows in by_key.items():
        us = [r for r in rows if market(r.campaign) != "Canada"]
        ca = len(rows) - len(us)
        if not us:
            continue
        mk = Counter(market(r.campaign) for r in us)
        rev = sum(r.amount for r in us)
        last = max((r.date for r in us if r.date), default=None)
        table.append((k, len(us), win(us, 90), win(us, 60), win(us, 30), rev, last, mk, ca))
    table.sort(key=lambda t: (-t[1], -t[3]))

    print("--- US paid sales per creative (Canada excluded) ---")
    print(f"  {'#':>2} {'life':>4} {'90d':>3} {'60d':>3} {'30d':>3} {'revenue':>9} {'last sale':>10} "
          f"{'spend RM':>9} {'leads':>5} {'RM/sale':>7} {'L→S':>5}  creative / markets / variants")
    for i, (k, life, d90, d60, d30, rev, last, mk, ca) in enumerate(table[:15], 1):
        sp, rg = spend.get(k, 0.0), regs.get(k, 0.0)
        cps = f"{sp / life:,.0f}" if sp else "—"
        ls = f"{life / rg * 100:.0f}%" if rg else "—"
        name = variants[k].most_common(1)[0][0]
        mks = ", ".join(f"{m} {n}" for m, n in mk.most_common())
        print(f"  {i:>2} {life:>4} {d90:>3} {d60:>3} {d30:>3} {rev:>9,.0f} {str(last):>10} "
              f"{sp:>9,.0f} {int(rg):>5} {cps:>7} {ls:>5}  {name}")
        print(f"      markets: {mks}" + (f" · +{ca} Canada sales not counted" if ca else "")
              + f" · spend from: {', '.join(sorted(accts.get(k, []))) or 'no US account match'}")
        if len(variants[k]) > 1:
            print(f"      merged {len(variants[k])} name variants: "
                  + " | ".join(f"{v} ({n})" for v, n in variants[k].most_common(5)))


if __name__ == "__main__":
    main()
