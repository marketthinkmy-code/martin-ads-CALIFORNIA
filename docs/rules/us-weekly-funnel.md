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

## Timing
- No scheduled start/end times on ad sets. The operator switches sides by hand on Malaysia
  Thursday morning (2026-11-04 decision).
- 加州 account time zone is Asia/Kuala_Lumpur; 美東美中 is America/New_York.

## Identity
- Every ad: Facebook Page **馬丁藥師｜兒童身高管理專家 `1180683238455992`** + Instagram
  **martinyaoshi.us**. API id `17841415309062626`; Ads Manager shows the same account as
  `36101311622850677` (the API rejects that format). Threads = use Instagram account.
  WhatsApp +60 11-2548 7541 comes from the Page link — verify on one ad after each build.
- **Always create new posts** (new creatives via object_story_spec). Do NOT reuse existing
  post IDs — this supersedes the existing-post approach in the East+Midwest handoff.

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
- Compliance: the operator reviewed the funnel doc's lines and chose to keep the original
  claims, including 「每年實現健康增高6cm-8cm」, ethnic/peer height comparison and the 醫師
  framing (2026-11-04). Brand number is 10,000+ 名孩子.

## Sales data
- Paid students: sheet tab `🇺🇸 Paid Student List ($799)`, matched by UTM ad name. Operator
  confirmed it is current as of 2026-11-04 (latest sale 2026-10-09).
- Rankings: `adbot-us-top-ads` workflow (merges name variants, excludes Canada).
