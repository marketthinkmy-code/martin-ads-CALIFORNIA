# US weekly funnel — operating rules (decided 2026-11-04)

Source plan: Google Doc "US 2days funnel" (北美华人孩子长高突围营). Earlier East+Midwest
history: docs/handoff/east-midwest-session.md. Where they conflict, this file wins.

## Rotation
- Free live session every **US Wednesday 8:00 PM local**, West and East+Midwest alternating.
- Only one side runs ads at a time. Operator turns the running side OFF on **Malaysia
  Thursday morning** (before the US-Wednesday live), then the other side goes ON, pointing at
  the next week's session.
- Ignore the four-day main-course dates for ad logic.

| | West | East+Midwest |
|---|---|---|
| Ad account | `act_1629566827721449` (加州) | `act_921653460987535` (美東美中) |
| Pixel | `1921735088376759` | `2035639583602118` |
| Landing page | https://kidsgrowthformula.com/register | https://kidsgrowthformula.com/us-register |
| Time zone rule | Pacific (PST) only | Eastern (EST) only |
| Geo | California + Washington + Doc cities (Cupertino, Fremont, Arcadia, Irvine, Walnut, Saratoga, Milpitas, Bellevue, Redmond) | Doc cities (West Windsor, East Brunswick, Princeton, Bayside, Fresh Meadows, Flushing, Lexington, Rockville, Potomac) + Eastern-time Midwest (Michigan, Ohio, Indiana) + Toronto/Ontario |
| Excluded | **Vancouver** (BC is UTC-7 since 2026-03-08, live would be 9 PM) | **Texas, Illinois, Minnesota** (Central time, live would be 7 PM) |

Toronto goes in the normal ad sets — no separate ad set.

## A/B test: state-level vs city-level
- Two campaigns per side, identical except geo.
- Campaign A = whole states/province, **excluding** campaign B's cities so audiences don't overlap.
- Campaign B = the cities (+ radius; Queens neighbourhoods by ZIP).
- Judge on CPL → show-up rate → cost per paid student, over 2–3 rotations, not one.

## Audiences
Test all three: Parents 3-17 + Engaged, Family and Relationships, Broad (Advantage+).

## Timing (US time, not account time)
- 加州 account time zone is **Asia/Kuala_Lumpur**; 美東美中 is America/New_York. Neither can be changed.
- Every ad set gets explicit `start_time` / `end_time` written with a US offset
  (West `-08:00` PST, East `-05:00` EST), so delivery starts/stops at the US moment
  regardless of account time zone.
- Ads end at the live start (Wed 8:00 PM local). The next side's ad sets start at the same moment.
- Daily budgets still reset at the account's midnight (加州: 00:00 MYT = 08:00 PST).

## Build rules
- **ABO, RM50/day per ad set**, one video per ad set, `is_adset_budget_sharing_enabled=False`.
- Objective OUTCOME_SALES, optimise CompleteRegistration on that side's pixel.
- Exclude people who registered in the last **15 days** (per-account website audience).
- Age 35–65, locales 20/21/22 (all Chinese), location type home + recent.
- Region / interest IDs resolved live and read back — never guessed.
- Built **PAUSED**; operator approves before anything goes live.
- UTM: `utm_source={{adset.name}}&utm_medium={{placement}}&utm_campaign={{campaign.name}}&utm_content={{ad.name}}`
- Naming prefix: `US West | …` and `US East+Midwest | …`; ad sets named after targeting.
- Videos uploaded via CI (the MCP upload path is not open on these accounts).

## Copy rules
- Name: **馬丁醫師**. Script: **繁體**. Punctuation: full-width （，。！？：）.
- Paragraph blocks, lines stacked inside a block, blank line only between blocks. No markdown.
- One best version only; show copy for approval before building.
- Compliance line the operator keeps (2026-11-04): **never promise a specific height gain**
  (no "每年長高 6–8cm"-style guarantees, no adult-height prediction). The operator explicitly
  allowed ethnic/peer height comparison and the 醫師 / health framing.

## Sales data
- Paid students: sheet tab `🇺🇸 Paid Student List ($799)`, matched by UTM ad name. Operator
  confirmed it is current as of 2026-11-04 (latest sale 2026-10-09).
- Rankings: `adbot-us-top-ads` workflow (merges name variants, excludes Canada).
