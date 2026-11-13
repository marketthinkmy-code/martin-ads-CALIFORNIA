# US weekly funnel — operating rules (decided 2026-11-04)

Source plan: Google Doc "US 2days funnel" (北美华人孩子长高突围营). Earlier East+Midwest
history: docs/handoff/east-midwest-session.md. Where they conflict, this file wins.

## Live schedule (operator, 2026-11-12) — Wednesdays 8–10 PM local, West / East alternating
| # | US date | MYT | Side | Owner |
|---|---|---|---|---|
| 1 | 2026-11-11 | 11/12 12:00 | West | Qing |
| 2 | 2026-11-18 | 11/19 09:00 | East | Shirley |
| 3 | 2026-12-02 | 12/3 12:00 | West | Qing |
| 4 | 2026-12-09 | 12/10 09:00 | East | Shirley |
| 5 | 2026-12-16 | 12/17 12:00 | West | Qing |
| 6 | 2026-12-23 | 12/24 09:00 | East | Shirley |
| 7 | 2027-01-06 | 1/7 12:00 | West | Qing |
| 8 | 2027-01-13 | 1/14 09:00 | East | Shirley |
| 9 | 2027-01-20 | 1/21 12:00 | West | Qing |
| 10 | 2027-02-03 | 2/4 09:00 | East | Shirley |
| 11 | 2027-02-10 | 2/11 12:00 | West | Qing |
| 12 | 2027-02-17 | 2/18 09:00 | East | Shirley |
| 13 | 2027-02-24 | 2/25 12:00 | West | Qing |
No live on 11/25 (Thanksgiving), 12/30 or 1/27 — those weeks have no side to promote, so the
"switch sides every Thursday" rule pauses; confirm each switch-on date with the operator.
Holiday weeks (Thanksgiving 11/26, Christmas Eve 12/24, New Year's Eve 12/31) need extra care
with attendance and ad costs.

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

During a one-week test CPA can't be judged, so in-week decisions are CPL-based
(operator, 2026-11-12 — replaces RM130/RM130, and before that RM150/RM170):
- 关: ad set spend ≥ RM100 with 0 registrations, or ≥ RM100 with CPL > RM100.
  Every ad set is judged on its own: no per-check limit, and NO "keep ≥ 1 per campaign"
  rule (removed by the operator 2026-11-12). If every ad set of a campaign gets paused, the
  campaign simply has nothing running — record that cell's result in the report.
- ⚠ flag only: CPL RM85–100.
- 开: no reopening during the week unless the operator asks.
- Scale: no budget changes during the week unless the operator asks. CPL ≤ RM85 with ≥ 3
  registrations → list it; next rotation that ad set gets +20% budget.
- CPA (≥ 14 days after the live and ≥ RM1,000 spend): ≤ RM1,300 healthy/scale, > RM1,700
  pause candidate, > RM2,200 with real sales = pause.

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
- 2026-11-11: East+Midwest history (register + paid tabs, Aug 22–Sep 16; tool
  adbot-em-adset-rank): all 3 East+Midwest paid sales came from Broad Advantage+ (RM8,478,
  112 registrations, CPL ~RM76); F&R CPL ~RM74 / 0 paid, Food & Drink ~RM94 / 0, Parents
  ~RM124 / 0. Operator approved a second new-video campaign `US East+Midwest | Broad A+ |
  新影片 V1–V8` (120255769879730558): 7 states + Ontario, no city exclusion, Advantage+ ON,
  8 × RM50, PAUSED. East+Midwest now 34 ad sets ≈ RM1,700/day if all on.
- 2026-11-11: operator chose to keep the Broad A+ new-video campaign on the whole region (no
  city exclusion) even though it overlaps every other East+Midwest campaign, including both
  sides of the state/city A/B. Read the A/B with that caveat.
- Spend note: EM now holds 18 + 8 = 26 ad sets (RM1,300/day if all on). Recommended at
  switch-on: old 城市级 9 + new 8 (≈ RM850/day); operator decides.

### West 11/4–11/12 result (CPL only; CPA verdict after 11/26 with the paid list)
- Total RM6,779 / 34 registrations (CPL ~RM199). All 7 US West campaigns paused at campaign
  level 2026-11-12 10:00 MYT (operator request).
- Geo: 城市级 RM3,179 / 18 (CPL ~177; + new-video campaign RM954 / 6) vs 州级 RM2,646 / 10
  (CPL ~265). City wins, but city also had Advantage+ ON and 州级 OFF.
- Cells: 城市级 F&R best (RM1,472 / 12, CPL ~123); 州级 F&R worst (RM659 / 0).
- Old videos: V4 RM1,521 / 10 (~152), V1 RM1,400 / 9 (~156), V3 RM1,121 / 5 (~224),
  V2 RM990 / 3 (~330, all from 州级 Parents), V10 RM793 / 1 (~793).
- New videos (city F&R, from 11/9): V8 RM174 / 3 (~58), V2 RM164 / 1, V5 RM156 / 1,
  V7 RM131 / 1, V1/V3/V4/V6 RM74–90 / 0 each.
- Lessons: too many ad sets at launch (22 → RM1,100+/day) burned budget before the rules
  could act; the KL-day timing gap let V2/V5 run past the line on live day (no check between
  21:13 MYT and the end of the US day) — add a mid-US-day check on the last two days.

### Approved for the next rotations (operator 2026-11-12: "下一场直播就执行所有你发现的和建议的")
Next West (live US Wed 2026-12-02 = MYT Thu 12/3 12:00; switch-on MYT Thu 2026-11-26 — operator
chose option A on 2026-11-12: a full 7 days, accepting Thanksgiving / Black Friday / Cyber Monday
CPMs; watch spend closely 11/26–11/30):
- City level is the core; F&R is the lead audience. State level keeps only Broad + Parents as
  the control — no 州级 F&R.
- Videos: keep old V4 + V1 and new Video 8; retest new Video 2 / 5 / 7; drop V10, old V2
  (except 州级 Parents V2) and new Video 1 / 3 / 4 / 6.
- Start with 10–12 ad sets (not 22). Copy + plan shown to the operator for approval first;
  build PAUSED; operator sets Strategy type + WhatsApp by hand.
- Monitoring: pause calls at the check before the US day starts (West 21:13 MYT, East
  19:13 MYT); on the last two US days before a live, add a mid-US-day check (West ~05:13 MYT,
  East ~02:13 MYT) so nothing runs past the line on live day; tighten early if the last days
  slow down.
- CPA verdict for the 11/4–11/12 West week ~2026-11-26 (14 days after the live) from the paid
  list; scale = CPL ≤ RM85 and ≥ 3 registrations → +20% (operator 2026-11-12).
East+Midwest (11/12–11/19) keeps all 34 ad sets (operator, 2026-11-11) — only the monitoring
lessons apply there.
- 2026-11-12: switched on 06:00 EST; by 08:52 EST it had spent RM1,518 (5 registrations, CPM
  RM170–300) — Meta front-loaded almost a full day's budget in ~3 h. Operator cut all 34 ad
  sets RM50 → RM35/day (≈ RM1,190/day) at ~22:00 MYT and asked to watch closely: EM checks
  run daily at 19:13 / 23:13 / 02:13 / 10:13 MYT (06:13 / 10:13 / 13:13 / 21:13 EST).
- 2026-11-12 ~22:10 MYT, reserve plan (operator): keep only the 5 ad sets with a registration
  running (Broad A+ 新V8, 城市级 F&R 新V6, 城市级 F&R V1, 城市级 Parents V3, 州级 Broad V4);
  pause the other 29 (0 registrations, RM1,349.71 spent) as reserve — not a rule-pause — and
  reopen them at the MYT Sat 11/14 19:13 check (06:13 EST), so the budget is spread over the
  week instead of burnt in the first days. After reopening they're judged by the normal rules
  with spend counted from 11/12.
- Correction ~22:20 MYT: Broad A+ 新V5 had a registration attributed after the read, so it was
  paused by mistake; reopened. The operator put these 6 ad sets back to RM50/day; the 28
  reserve ad sets stay at RM35. Late attribution: re-read registrations right before pausing.
- 11/13: 4 more reserve ad sets showed late registrations (城市级 Broad V3, 城市级 F&R V3, 城市级
  F&R 新V8, 城市级 Parents V1). Operator: reopen them at RM50 only after EST day 1 is over
  (「等 day 1 过完再开」 — day 1 had already spent its budget) → MYT 11/13 13:13.
- 11/13 ~10:15 MYT, operator decision (goal: control spend and CPL): day 1 = RM1,920 / 11
  registrations (CPL ~RM175); the 24 zero-registration reserve ad sets had spent RM1,221 with 0
  registrations, the 10 with registrations CPL ~RM60–66. → CANCEL the 11/14 reserve reopen; run
  only the 10 ad sets with registrations (RM50 each) to the live; pause line stays RM100 (RM85
  tightening not taken). Safety valve, ask first: if < 4 running ad sets and < 3 registrations
  a day by ~11/16, propose reopening the 2–3 reserve ad sets with the most landing page views at
  RM35.
- Lesson: on a 34-ad-set launch, most of the first-morning money went to ad sets that never
  converted; next time launch fewer ad sets (proven cells: 城市级, Broad A+, 新V8, V3) and cut
  zero-registration ad sets early.
- Lesson for future switch-ons: start new ad sets at a lower budget (~RM35) and let Meta
  pace; a fresh launch burns its first day's budget in the first US morning hours.

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
