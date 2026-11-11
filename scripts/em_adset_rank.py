"""Read-only: rank US East+Midwest ad sets / audiences by real registrations and paid sales.

Reads every tab of the 马丁 Register and OTO, Purchase list workbook (cpa.spreadsheet_id),
keeps rows whose UTM campaign is an East+Midwest campaign, and counts registrations (register
tabs) and paid sales (paid / purchase tabs) per (campaign, ad set) and per audience bucket.
Joins lifetime Meta spend + pixel registrations per ad set from the 美東美中 account, so each
ad set gets CPL, cost per sale and lead→sale %.

Prints tab names, header labels, ad set names and counts only — no customer data.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import load_settings

ACCT = "act_921653460987535"


def is_em(campaign: str) -> bool:
    c = cpa.norm(campaign)
    return "east" in c and "midwest" in c


def bucket(adset: str) -> str:
    a = cpa.norm(adset)
    if "parent" in a:
        return "Parents 3-17 + Engaged"
    if "food" in a or "milk" in a or "bread" in a:
        return "Food & Drink / Milk / Bread"
    if "family" in a or "f&r" in a or "relationship" in a:
        return "Family and Relationships"
    if "broad" in a or "advantage" in a:
        return "Broad (Advantage+)"
    return f"other: {adset or '(no ad set)'}"


def kind(tab: str) -> str:
    t = cpa.norm(tab)
    if any(w in t for w in ("paid", "purchase", "student", "$", "付款", "成交")):
        return "paid"
    if any(w in t for w in ("register", "regist", "报名", "報名", "lead", "webinar")):
        return "register"
    return "other"


def main() -> None:
    s = load_settings()
    sh = SheetsClient(s.secrets.google_sa_json)
    sid = s.cpa.spreadsheet_id
    regs = defaultdict(int)       # (campaign, adset) -> sheet registrations
    paid = defaultdict(int)
    rev = defaultdict(float)
    dates = defaultdict(list)
    print("=== tabs ===")
    for tab in sh.tab_titles(sid):
        try:
            values = sh.read_tab(sid, tab)
            rows, cols, header = cpa.parse_sales(values, s.cpa.price_myr)
        except Exception as e:  # noqa: BLE001
            print(f"  [{tab}] unreadable: {str(e)[:80]}")
            continue
        k = kind(tab)
        em = [r for r in rows if is_em(r.campaign)]
        found = {n: (header[i] if 0 <= i < len(header) else "-") for n, i in cols.items()}
        print(f"  [{tab}] kind={k} rows={len(values)} utm-rows={len(rows)} EM-rows={len(em)} "
              f"cols={found}")
        if k not in ("paid", "register"):
            continue
        for r in em:
            key = (r.campaign, r.adset)
            if k == "paid":
                paid[key] += 1
                rev[key] += r.amount
            else:
                regs[key] += 1
            if r.date:
                dates[key].append(r.date)

    print("\n=== Meta lifetime spend per East+Midwest ad set ===")
    g = graph_client(s)
    tok = result_action_type(s.meta.conversion_event)
    spend, mregs, names = defaultdict(float), defaultdict(float), {}
    for r in g.account_insights(ACCT, level="adset",
                                fields="campaign_name,adset_name,adset_id,spend,actions",
                                date_preset="maximum"):
        key = (cpa.norm(r.get("campaign_name", "")), cpa.norm(r.get("adset_name", "")))
        spend[key] += float(r.get("spend") or 0)
        mregs[key] += float(extract_results(r.get("actions"), tok) or 0)
        names[key] = (r.get("campaign_name", ""), r.get("adset_name", ""))

    keys = set(regs) | set(paid) | {k for k in spend if spend[k] > 0}
    table = []
    for key in keys:
        sp, sr, mr, pd = spend.get(key, 0.0), regs.get(key, 0), mregs.get(key, 0.0), paid.get(key, 0)
        ds = sorted(dates.get(key, []))
        table.append((pd, sr, sp, mr, key, ds[0] if ds else None, ds[-1] if ds else None))
    table.sort(key=lambda t: (-t[0], -t[1], t[2]))

    def f(x, d=0):
        return f"{x:,.{d}f}"

    print(f"\n=== AD SETS (East+Midwest campaigns) — sorted by paid sales, then sheet registrations ===")
    print(f"  {'paid':>4} {'sheetReg':>8} {'metaReg':>7} {'spend RM':>9} {'CPL':>6} {'RM/sale':>8} "
          f"{'L→S':>5} {'first':>10} {'last':>10}  campaign | ad set")
    for pd, sr, sp, mr, key, d0, d1 in table:
        lead = sr or mr
        cpl = f(sp / lead) if sp and lead else "—"
        cps = f(sp / pd) if sp and pd else "—"
        ls = f"{pd / lead * 100:.0f}%" if lead and pd else "—"
        c, a = names.get(key, key)
        print(f"  {pd:>4} {sr:>8} {int(mr):>7} {f(sp):>9} {cpl:>6} {cps:>8} {ls:>5} "
              f"{str(d0):>10} {str(d1):>10}  {c} | {a}")

    agg = defaultdict(lambda: [0, 0, 0.0, 0.0, set()])
    for pd, sr, sp, mr, key, _, _ in table:
        b = bucket(names.get(key, key)[1])
        x = agg[b]
        x[0] += pd; x[1] += sr; x[2] += sp; x[3] += mr; x[4].add(key[0])
    print("\n=== BY AUDIENCE (East+Midwest) ===")
    print(f"  {'paid':>4} {'sheetReg':>8} {'metaReg':>7} {'spend RM':>9} {'CPL':>6} {'RM/sale':>8} {'L→S':>5}  audience (campaigns)")
    for b, (pd, sr, sp, mr, cs) in sorted(agg.items(), key=lambda kv: (-kv[1][0], -kv[1][1])):
        lead = sr or mr
        cpl = f(sp / lead) if sp and lead else "—"
        cps = f(sp / pd) if sp and pd else "—"
        ls = f"{pd / lead * 100:.0f}%" if lead and pd else "—"
        print(f"  {pd:>4} {sr:>8} {int(mr):>7} {f(sp):>9} {cpl:>6} {cps:>8} {ls:>5}  {b} ({len(cs)})")
    print(f"\nTotals: paid {sum(paid.values())}, sheet registrations {sum(regs.values())}, "
          f"Meta spend RM{sum(spend.values()):,.0f}")


if __name__ == "__main__":
    main()
