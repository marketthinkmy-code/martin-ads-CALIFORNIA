"""Read-only: LEAD QUALITY vs SPEND allocation audit.

Operator hypothesis: recent trouble is a LEAD-QUALITY problem — ads that register cheap leads
that never buy — and the profitable ads may have been UNDER-funded while money flowed to
low-quality-lead ads.

This joins, per ad, over LIFETIME (date_preset=maximum):
  - spend + registrations (leads)  ← Meta ad-level insights
  - real paid sales (buyers)        ← Paid Student List tab, matched by UTM ad name
and computes the quality + efficiency metrics that CPL alone hides:
  - lead→sale %  = sales / registrations   (LEAD QUALITY: how many leads actually buy)
  - cost / sale  = spend / sales           (the number that actually matters)
  - cost / lead  = spend / registrations   (CPL, for reference)

Then it exposes the MISALLOCATION directly:
  - "where the money went"   = ads ranked by spend
  - "where the buyers came"  = ads ranked by sales
  - underfunded winners  (many sales, good lead→sale%, but low spend share)
  - overfunded low-quality (high spend, many leads, few/no sales)

No writes. Run via the adbot-lead-quality workflow.
"""
from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import load_settings


def _money(x):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def _ratio(n, d):
    return (n / d) if d else None


def _fmt_pct(v):
    return "—" if v is None else f"{v*100:.1f}%"


def _fmt_money(v):
    if v is None:
        return "—"
    return "∞" if v == math.inf else f"{v:,.0f}"


def main() -> None:
    s = load_settings()
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()  # MYT
    g = graph_client(s)
    acct = s.meta.account_path
    token = result_action_type(s.meta.conversion_event)

    # ── 1. lifetime spend + registrations per ad (Meta) ──────────────────────
    spend_by_ad, reg_by_ad, name_by_ad, camp_by_ad = {}, {}, {}, {}
    for r in g.account_insights(acct, level="ad",
                                fields="ad_id,ad_name,campaign_name,spend,actions",
                                date_preset="maximum"):
        aid = r.get("ad_id")
        if not aid:
            continue
        spend_by_ad[aid] = _money(r.get("spend"))
        reg_by_ad[aid] = float(extract_results(r.get("actions"), token) or 0)
        name_by_ad[aid] = r.get("ad_name", aid)
        camp_by_ad[aid] = r.get("campaign_name", "")

    # currently-ACTIVE ad names (so we can mark live vs off)
    active_adnorms = set()
    for camp in g.list_campaigns(acct):
        if camp.get("effective_status") != "ACTIVE":
            continue
        for ad in g.list_ads_under_campaign(camp["id"]):
            if ad.get("effective_status") == "ACTIVE":
                active_adnorms.add(cpa.norm(ad.get("name", "")))

    # ── 2. lifetime paid sales per ad (sheet, matched by UTM ad name) ─────────
    sheets = SheetsClient(s.secrets.google_sa_json)
    values = sheets.read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab)
    sales, cols, hdr = cpa.parse_sales(values, s.cpa.price_myr)
    attributed = [x for x in sales if x.ad]
    sales_by_norm = defaultdict(int)
    for x in attributed:
        sales_by_norm[cpa.norm(x.ad)] += 1

    print(f"=== LEAD QUALITY vs SPEND · lifetime · today MYT={today} ===")
    print(f"Paid tab '{s.cpa.sales_tab}': {len(values)} rows · {len(attributed)} sales carry an ad name")
    print(f"Meta ads with lifetime spend: {len(spend_by_ad)}\n")
    if not attributed:
        print("⚠️  No sales carry an ad name — cannot measure lead quality. Stopping.")
        return

    # ── 3. per-ad join by normalized ad name ─────────────────────────────────
    rows = []  # (norm, camp, spend, reg, sales, lead_sale, cost_sale, cpl, live)
    seen = set()
    for aid, spend in spend_by_ad.items():
        norm = cpa.norm(name_by_ad[aid])
        seen.add(norm)
        sold = sales_by_norm.get(norm, 0)
        reg = reg_by_ad.get(aid, 0)
        rows.append((norm, camp_by_ad.get(aid, ""), spend, reg, sold,
                     _ratio(sold, reg), (spend / sold) if sold else (math.inf if spend else None),
                     _ratio(spend, reg), norm in active_adnorms))
    # sales attributed to ad names Meta lifetime insights didn't return (very old / renamed)
    for norm, sold in sales_by_norm.items():
        if norm not in seen:
            rows.append((norm, "?", 0.0, 0, sold, None, 0.0, None, norm in active_adnorms))

    total_spend = sum(r[2] for r in rows)
    total_sales = sum(r[4] for r in rows)
    total_reg = sum(r[3] for r in rows)
    print(f"TOTALS · spend RM{total_spend:,.0f} · {int(total_reg)} leads · {total_sales} sales · "
          f"blended lead→sale {_fmt_pct(_ratio(total_sales, total_reg))} · "
          f"cost/sale RM{_fmt_money(_ratio(total_spend, total_sales))}\n")

    # ── A. where the MONEY went (ranked by spend) ────────────────────────────
    print("--- WHERE THE MONEY WENT (top 20 by lifetime spend) ---")
    print(f"  {'ad':40} {'spend':>8} {'leads':>5} {'sale':>4} {'L→S':>6} {'/sale':>7} {'/lead':>6} live")
    for norm, camp, spend, reg, sold, ls, cps, cpl, live in sorted(rows, key=lambda r: -r[2])[:20]:
        print(f"  {norm[:40]:40} {spend:8,.0f} {int(reg):5d} {sold:4d} {_fmt_pct(ls):>6} "
              f"{_fmt_money(cps):>7} {_fmt_money(cpl):>6} {'●' if live else ' '}")

    # ── B. where the BUYERS came from (ranked by sales) ──────────────────────
    print("\n--- WHERE THE BUYERS CAME FROM (top 20 by lifetime sales) ---")
    print(f"  {'ad':40} {'sale':>4} {'spend':>8} {'/sale':>7} {'L→S':>6} {'leads':>5} live")
    for norm, camp, spend, reg, sold, ls, cps, cpl, live in sorted(rows, key=lambda r: -r[4])[:20]:
        if sold <= 0:
            break
        print(f"  {norm[:40]:40} {sold:4d} {spend:8,.0f} {_fmt_money(cps):>7} {_fmt_pct(ls):>6} "
              f"{int(reg):5d} {'●' if live else ' '}")

    # ── C. UNDERFUNDED WINNERS — high sales, but small share of spend ────────
    # heuristic: made >=2 sales, cost/sale beats blended, yet spent < median of sellers
    sellers = [r for r in rows if r[4] >= 1 and r[2] > 0]
    blended_cps = _ratio(total_spend, total_sales) or math.inf
    spends_sorted = sorted(r[2] for r in sellers)
    med_spend = spends_sorted[len(spends_sorted)//2] if spends_sorted else 0
    print("\n--- ⭐ UNDERFUNDED WINNERS (good cost/sale, but low spend — SCALE THESE) ---")
    uf = [r for r in sellers if r[6] not in (None, math.inf) and r[6] <= blended_cps and r[2] < med_spend]
    for norm, camp, spend, reg, sold, ls, cps, cpl, live in sorted(uf, key=lambda r: r[6])[:12]:
        print(f"  {sold:>2} sales · RM{cps:,.0f}/sale · only RM{spend:,.0f} spent · L→S {_fmt_pct(ls)} · "
              f"{'●LIVE' if live else 'off'}  {norm[:40]}")
    if not uf:
        print("  (none)")

    # ── D. OVERFUNDED LOW-QUALITY — high spend, weak/no sales ────────────────
    print("\n--- ✗ OVERFUNDED LOW-QUALITY (big spend, few/no sales — CUT/RETHINK) ---")
    of = [r for r in rows if r[2] >= max(med_spend, 300) and (r[6] in (None, math.inf) or r[6] > blended_cps)]
    for norm, camp, spend, reg, sold, ls, cps, cpl, live in sorted(of, key=lambda r: -r[2])[:12]:
        print(f"  RM{spend:,.0f} spent · {sold} sales · {_fmt_money(cps)}/sale · {int(reg)} leads · "
              f"L→S {_fmt_pct(ls)} · {'●LIVE' if live else 'off'}  {norm[:40]}")
    if not of:
        print("  (none)")


if __name__ == "__main__":
    main()
