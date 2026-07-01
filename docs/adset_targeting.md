# Ad-set targeting playbook — Martin California (operator's manual setup)

This is the post-build checklist for every California `1-1-N` ad set. The bot's `build`
applies the broad Advantage+ settings automatically (see *Encoding status*); the
**city-level geo** is the one thing it cannot apply and you must set manually.

## The settings

### 1. Customer lifecycle strategy = "Get conversions from all audiences"
Advantage+ Sales Campaign (ASC) ad-set control. "All audiences" = no new-vs-existing
budget split — Meta optimizes across everyone, and the **exclusions** below do the
"reach fresh prospects" filtering instead.

### 2. Advantage+ audience = ON
`targeting_automation.advantage_audience = 1`. With it ON, age / locale become
**suggestions**, not hard caps — Meta can expand beyond them. Min age shows **25**
(a suggestion). Do NOT raise `age_min` as a hard floor or Meta rejects it
(*"You can add a higher minimum age as a suggestion instead"*).

### 3. Exclusions (`excluded_custom_audiences`) — drop existing registrants
| Audience | ID | Type |
|---|---|---|
| US 15days complete registration | `120236056842490259` | PLATFORM (website / pixel) |

Purpose: don't pay to reach people who already registered.

### 4. ⚠️ CITY-LEVEL GEO — set MANUALLY in Ads Manager (code cannot apply this)
The California audience framework (`config/audience.md`) is explicit: **state/province-level
targeting is the root cause of high CPL** — it wastes budget on non-Chinese reach. You must
narrow to Chinese-dense CALIFORNIA CITIES. The adbot `Targeting` model only emits
`geo_locations.countries` (`["US"]`), so after `build` and before activating, edit each ad
set's location in Ads Manager to city-level:

> Arcadia · San Marino · San Gabriel · Monterey Park · Cupertino · Fremont · Irvine
> (plus any other SGV / Bay Area Chinese-dense cities the operator wants)

Stack the language filter (Chinese, locale 1004) + parent targeting on top.

## Encoding status — auto-applied by `build`
`settings.Targeting.to_spec()` emits these from `config.yaml > meta.targeting`:
- `geo_locations.countries = ["US"]` (country-level only — **narrow to cities manually**),
- `advantage_audience = 1` with `age_min = 25` (suggestion, not a hard floor),
- `locales = [1004]` (Chinese All),
- `excluded_custom_audiences` = the id above.

"Get conversions from all audiences" needs **no field** — it is the default ASC lifecycle when
no existing-customer budget cap is set, and `build` never sets one.

## Webinar timing note
Per the framework, the webinar runs PDT 8 PM. Keep delivery/scheduling aligned with the
Pacific timezone audience.

## Safety
`build` reuses an existing ad set **by ID** and never rewrites its targeting on reuse; the
monitor cron only changes **budget / status**, never targeting. So nothing the bot does will
undo your manual city-level edits.
