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

Advantage+ audience (US West build, 2026-11-04, operator's choice — keep as is):
- 城市级 ad sets: Advantage+ audience ON (Meta flagged the audience as too small);
  age_min 25 with 35–65 as a suggestion. Location stays a hard limit, so the 9 cities
  are still the only geo and the 州级 city exclusion still holds.
- 州级 ad sets: Advantage+ audience OFF, age 35–65 fixed.
- Caveat when reading results: 州级 vs 城市级 now differ in geo AND Advantage+.

## Monitoring (US West A/B, confirmed by operator 2026-11-04; revisit later)
Checks at 10:13 / 16:13 / 21:13 MYT, report in 华语. Account rules (config/config.yaml):
CPL line RM85 is advisory only (auto-pause on CPL was turned off 2026-07-24 because it
killed paid winners); CPA target RM1,000, ≤ RM1,300 healthy, > RM1,700 pause candidate,
> RM2,200 with real sales = pause; CPA judged only after 14 days and ≥ RM1,000 spend.

During a one-week test CPA can't be judged, so in-week decisions are CPL-based:
- 关: ad set spend ≥ RM130 with 0 registrations, or ≥ RM130 with CPL > RM130
  (operator, 2026-11-09 evening; earlier the same day RM150/RM150, before that RM150/RM170).
  No per-check limit — pause every ad set that meets the criteria (operator, 2026-11-07;
  replaces the earlier max-3 cap). Keep ≥ 1 ad set running in every campaign so each test cell keeps data —
  EXCEPT when all 3 ad sets in a campaign meet the pause criteria: that cell has lost, so
  pause the whole campaign and record the verdict with its CPL (operator, 2026-11-06).
- ⚠ flag only: CPL RM85–130, or RM100–130 spent with 0 registrations.
- 开: no reopening during the week unless the operator asks.
- Scale: no budget changes during the test week; list candidates (CPL ≤ RM85, ≥ 3 reg).
  Next rotation: CPL ≤ RM85 and ≥ 5 reg → +20–30% budget; CPA ≤ RM1,300 → scale.

### Operator decisions during the 11/4–11/12 West test
- 2026-11-07: operator paused the 8 old ad sets with 0 registrations at ~RM133–145.
- 2026-11-08: operator chose to pause the 5 zero-registration V10 ad sets early (V10: 1 reg on
  ~RM693) and the whole 州级 F&R campaign (verdict: lost — 0 registrations on ~RM645 across
  V1/V3/V4/V2/V10). Operator raised 城市级 F&R V4 (3 reg, CPL RM61) from RM50 to RM65/day —
  an approved exception to "no budget changes during the test week".
- 2026-11-09 (12:30 MYT): 11/8 spent RM1,255 for 3 registrations (CPL RM418) — RM620 of it on
  14 ad sets that were paused only after the US day had already run (0 registrations). To cap
  spend before the 11/11 live, operator chose plan "D": pause the 3 CPL ~RM130 ad sets
  (城市级 Broad V1, 城市级 F&R V3, 城市级 Parents V3 — this leaves 城市级 Broad and 城市级 Parents
  with nothing running; operator accepted losing those cells' data), raise 城市级 F&R V1
  (5 reg, CPL RM54) RM50→RM65 and 州级 Parents V2 (3 reg, CPL RM64) RM50→RM60. Running after:
  4 ad sets, RM240/day.
- 2026-11-11 (15:41 MYT, just before the live-day US morning): results worsened (11/10 RM631 /
  3 reg; 11/11 to 10:13 RM298 / 0 reg; pixel healthy). Operator paused 7 ad sets early, before
  they reached the rule line: new V1/V3/V4/V6 (0 reg on RM66–82 each), 州级 Parents V2 (3 reg,
  CPL ~RM114), 城市级 F&R V4 (4 reg, ~RM103), 州级 Broad V4 (4 reg, ~RM100). Kept: 城市级 F&R V1
  (6 reg, CPL ~RM71) + new V2/V5/V7/V8 (1 reg each) ≈ RM185/day.
- 2026-11-11: East+Midwest — operator decided to switch on everything as built (18 state/city
  A/B ad sets + all 8 new-video ad sets at RM50, ≈ RM1,300/day), NOT trimmed by West results,
  so EM runs its own full test. Switch-on: Thu 11/12 13:00 MYT (EST midnight = start of the EM
  account day), after setting Strategy type + WhatsApp on all 26 in the morning.
- Lesson (timing): the 加州 account's day is Asia/KL, so the US day (08:00–24:00 PST) is
  KL 00:00–16:00. A pause decided at the 10:13 or 16:13 check comes after that day's money is
  spent. Make pause calls at the 21:13 MYT check, before the US day starts.

### East+Midwest new-video build (2026-11-09, for the 11/18 live)
- Operator approved copy + plan: campaign `US East+Midwest | 城市级 | F&R | 新影片 V1–V8`
  (120255732277170558), 8 ad sets × RM50 (RM400/day), PAUSED. Targeting cloned from the
  EM 城市级 F&R V1 ad set (West's winning cell). Per-video copy: scripts/new8_copy.py.
- Ad names = operator's script titles ("Video 3：完蛋了！"). Drive files "Martin Sep Video
  0N" = Video N — confirmed by speech-to-text of each opening (adbot-drive-video-frames)
  before the build. Old and new "Video N" share numbers but are different videos.
- West copy of the same build (operator, 2026-11-09): `US West | 城市级 | F&R | 新影片 V1–V8`
  (120249156726090259), 8 ad sets × RM50, PAUSED, /register, targeting cloned from West
  城市级 F&R V1 (incl. its 4 paid-list/registrant exclusions). Same 8 videos attached by id
  from the 美東美中 uploads. If the operator switches any of it on during a West week, the
  scheduled checks monitor those ad sets under the same rules.
- 2026-11-09 evening: operator switched on the West new-video campaign (edited the creatives
  in Ads Manager first) and cut its 8 ad sets from RM50 to RM30/day. West running: old 4
  (RM240) + new 8 (RM240) = RM480/day. At RM30/day a new ad set needs ~5 days to reach the
  RM150 pause line, so this week they are mostly flag-only.
- 2026-11-11 operator decision: East+Midwest is judged on its own — do NOT carry West results
  over. Keep all 26 ad sets (18 state/city A/B + 8 new videos, RM50 each, ≈ RM1,300/day) and
  run the full state-vs-city A/B there too. Switch-on: Thu 2026-11-12 13:00 MYT (midnight EST,
  start of the account day), after setting Strategy type + WhatsApp by hand.
- Spend note: EM now holds 18 + 8 = 26 ad sets (RM1,300/day if all on). Recommended at
  switch-on: old 城市级 9 + new 8 (≈ RM850/day); operator decides.

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

## After every build — operator sets these by hand (2026-11-06)
The API route for these two was not found (WhatsApp `wamo_whatsapp_identity_spec` read back
empty even on operator-edited creatives; no strategy-type field showed in the ad set diff).
The operator chose to keep doing them by hand, so every build report must remind them:
1. **Customer life cycle strategy → Strategy type = "Get conversions from all audiences"**
   on every new ad set.
2. **Identity → WhatsApp phone number = +60 11-2548 7541** on every new ad (Page
   馬丁藥師｜兒童身高管理專家, Instagram martinyaoshi.us, Threads = Use Instagram account).
3. **Publish** after editing (Ads Manager saves bulk edits as a draft first).
If a later before/after read-back on one object reveals the fields, automate them then.
Tool for that: `adbot-diff-object-fields` with `only_fields` (cheap; the full dump gets
rate-limited).

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
