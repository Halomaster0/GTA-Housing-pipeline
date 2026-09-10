# Design plan — GTA Housing Pipeline public web app

**Status: PROPOSAL — awaiting review by `director-product-frontend`, per Gate 1 and Gate 4b criteria in `docs/build-plan.md`.**
**Date: 2026-09-10 · Author: `design-lead` · Pass 1 + Pass 2 (self-critique) both included below, as required before any UI code is written.**

Nothing in this document is implemented. No CSS, no components, no `web/styles/tokens.css` exist yet — this file is the plan those things get built from, once approved. All figures shown inside the wireframes below (row counts, scores, dates, trace IDs) are illustrative placeholders for layout purposes only. They are not measurements, and nothing in the shipped app may render a placeholder like this as if it were real — every number on the live site comes from a manifest, a results file, or a live query, or the component renders its empty state instead.

---

## 1. Principles

The palette, type, and grid come from the actual paper trail this project ingests — zoning-map land-use fills, survey-plat linework, and blueprint drafting conventions — so the visual system carries information (register red means refusal, permit gold means residential permit volume) instead of decorating an otherwise generic layout on top of it. The one visually rich surface on the whole site is the live GTA municipality map on the landing page, rendered from real gold-layer data; every other surface — buttons, tables, chips, tiles, panels — is flat, bordered, and quiet, because a hiring manager evaluating engineering judgment in ninety seconds should notice the evidence, not the interface around it. Every route defaults to showing its real number or its real absence — an explicit "not yet measured," "no rows returned," or "source is stale" — instead of a plausible placeholder, because the truth discipline that governs the README and the eval report (§4, §9 R11/R12 in `docs/build-plan.md`) has to govern the pixels too, or the site quietly contradicts the project's own thesis.

---

## 2. Palette

The source material is the specific colour language of municipal planning documents: zoning-map land-use fills, survey-plat ink, and the two-tone reversal of blueprint (cyanotype) drafting prints — white or cream linework on a deep blue ground, which is where the word "blueprint" comes from. Six named values, each doing one job, specified for light and dark:

| Name | Role | Light hex | Dark hex | Rationale |
|---|---|---|---|---|
| **Surface** | Page background | `#F6F5F0` (Paper) | `#10233A` (Blueprint) | Paper is bond/drafting-plot paper — the stock a zoning map or site plan gets printed on — deliberately cooler and less nostalgic than a cream/parchment tone. Blueprint is the literal cyanotype ground of an engineering print, not a generic near-black. |
| **Ink** | Primary text, linework, borders | `#1C1E1B` (Ink) | `#EDEAE0` (Linework) | India-ink black used for plat annotations and survey linework; on Blueprint it reverses to the warm off-white a blueprint's lines are actually printed in. |
| **Survey Blue** | Links, primary interactive elements, focus ring | `#1F4E79` (Survey Blue) | `#8FC1E8` (Ice Blue) | The institutional/civic land-use fill from a municipal zoning legend, reused as the site's only interactive colour so a link reads as "this is the official record," not "this is a button." |
| **Register Red** | Refusal state, error state — used sparingly | `#A93226` (Register Red) | `#E2685A` (Register Red Dark) | The ink colour of a registry stamp — "RECEIVED," "APPROVED," a date seal. Reserved for the one correctly-refused example query and genuine failures. It never decorates a heading or a button that isn't reporting one of those two things. |
| **Parcel Green** | Positive/healthy state | `#3F6B4A` (Parcel Green) | `#8FCB98` (Parcel Green Dark) | The open-space/park land-use fill from the same zoning legend, reused for "this source is live," "this eval bucket passed." |
| **Permit Gold** | Data accent — chart fills, the map, permit-volume figures | `#8A5A17` (Permit Gold, for text) / `#9C6B1E` (Permit Gold Fill, for large fills/graphics) | `#E7BE63` (Permit Gold Dark) | The residential land-use fill from the zoning legend. It is the palette's most-used data colour precisely because permit volume is the project's most-used data — the colour a planner would actually use to mark a residential parcel is the colour this site uses to chart residential permits. |

A seventh tone — the rule line used for table borders and dividers — is not a named palette value; it is Ink at reduced strength (`#8B8779` light / `#54728F` dark), computed only so it clears the 3:1 UI-boundary minimum (below).

### Contrast — computed, not asserted

Ratios below were computed from the WCAG relative-luminance formula (sRGB → linear, `L = 0.2126R + 0.7152G + 0.0722B`, ratio = `(L_lighter + 0.05) / (L_darker + 0.05)`), not eyeballed. Script and output are reproducible; see the calculation note at the end of this section.

**Light mode (background: Paper `#F6F5F0`)**

| Foreground | Use | Ratio | Clears |
|---|---|---|---|
| Ink `#1C1E1B` | Body text | 15.38:1 | 4.5:1 body ✓ |
| Ink-secondary `#52564E` | Muted/secondary text | 6.87:1 | 4.5:1 body ✓ |
| Register Red `#A93226` | Accent text (refusal label) | 6.07:1 | 4.5:1 body ✓ |
| Survey Blue `#1F4E79` | Link text | 7.94:1 | 4.5:1 body ✓ |
| Parcel Green `#3F6B4A` | Accent text | 5.64:1 | 4.5:1 body ✓ |
| Permit Gold `#8A5A17` | Accent text | 5.41:1 | 4.5:1 body ✓ |
| Permit Gold Fill `#9C6B1E` | Chart fill / large graphic element | 4.24:1 | 3:1 large/UI ✓ |
| Rule line `#8B8779` | Table borders, dividers | 3.29:1 | 3:1 UI boundary ✓ |
| Ink `#1C1E1B` | Focus ring | 15.38:1 | 3:1 UI boundary ✓ (large margin) |

**Buttons (solid fill, white or Paper text on accent):**

| Pair | Ratio | Clears |
|---|---|---|
| Survey Blue fill + white text | 8.66:1 | 4.5:1 ✓ |
| Register Red fill + white text | 6.62:1 | 4.5:1 ✓ |

**Dark mode (background: Blueprint `#10233A`)**

| Foreground | Use | Ratio | Clears |
|---|---|---|---|
| Linework `#EDEAE0` | Body text | 13.18:1 | 4.5:1 body ✓ |
| Secondary text `#B7C4CE` | Muted/secondary text | 8.92:1 | 4.5:1 body ✓ |
| Register Red Dark `#E2685A` | Accent text (refusal label) | 4.81:1 | 4.5:1 body ✓ (tightest pair in the system — do not darken further) |
| Ice Blue `#8FC1E8` | Link text | 8.28:1 | 4.5:1 body ✓ |
| Parcel Green Dark `#8FCB98` | Accent text | 8.43:1 | 4.5:1 body ✓ |
| Permit Gold Dark `#E7BE63` | Accent text, chart fill | 9.02:1 | 4.5:1 body ✓ |
| Rule line dark `#54728F` | Table borders, dividers | 3.16:1 | 3:1 UI boundary ✓ |
| Linework `#EDEAE0` | Focus ring | 13.18:1 | 3:1 UI boundary ✓ |
| Linework fill `#EDEAE0` + Blueprint text | Primary button, dark mode | 13.18:1 | 4.5:1 ✓ |

Every pair actually used for text or a UI boundary clears its threshold, with one pair (Register Red Dark on Blueprint, 4.81:1) close enough to the 4.5:1 floor that it must not be reused at a lower size or a lighter weight than specified in §3 — flag this as the one colour in the system with no headroom to spare.

*Calculation note: computed with a small Python script implementing the WCAG 2.x relative-luminance and contrast-ratio formulas exactly as specified, run against every foreground/background pair above. Not included in the repo — this is a design artifact, not implementation — but any reviewer can re-derive the same numbers from the hex values and the formula cited above.*

---

## 3. Typography

**Two families, one functional third for data.**

1. **IBM Plex Sans Condensed** — headings, navigation, buttons, table headers, form labels, captions, metric-tile labels. Rationale: single-stroke engineering lettering — the lettering standard actually taught for dimensioning and annotating technical drawings — is narrow, mechanical, and built to stay legible at small sizes inside a title block. Plex Sans Condensed is the closest widely-available web font to that register without resorting to a literal stencil face, which would read as costume rather than convention.
2. **Source Serif 4** — long-form prose only: the `/architecture` write-up, `/evals` methodology paragraphs, ADR excerpts. Rationale: statutory notices, by-law text, and land-registry certificates are set in a plain workhorse serif meant for extended reading, not a display face. Source Serif 4's low stroke contrast and open counters read as "official document body copy," which is the register being borrowed — deliberately *not* a high-contrast editorial serif (see §Pass 2, item 1).
3. **IBM Plex Mono** — every SQL block, every numeric table column, trace IDs, timestamps, coordinates, latency and cost figures, and every large numeral in a metric tile. Rationale: parcel numbers, plan numbers, and legal descriptions on survey documents were traditionally typewritten, and tabular numerals need fixed width to align in a column regardless of tradition — both reasons point the same direction.

**What this deliberately excludes, and why:**
- **No high-contrast display serif for headings.** Pairing a serif headline with a light background is the single most common generic-AI-portfolio signature (see Pass 2, item 1). Headings are Plex Sans Condensed everywhere, with no exception.
- **No rounded/humanist default sans** (the Inter/Poppins-adjacent family every SaaS product reaches for). It reads as consumer software, not an engineering register.
- **No italic serif for emphasis inside prose beyond standard citation use** — italics are reserved for the handful of places prose actually needs them (a term being defined, a source title), not for decorative emphasis.

### Type scale

| Token | Family | Weight | Size | Line-height | Letter-spacing | Used for |
|---|---|---|---|---|---|---|
| display-metric | Plex Mono | Medium 500 | 2.5rem / 40px | 1.1 | 0 | Large numerals in metric tiles |
| h1 | Plex Sans Condensed | SemiBold 600 | 2rem / 32px | 1.15 | 0 | Page title (one per route) |
| h2 | Plex Sans Condensed | SemiBold 600 | 1.5rem / 24px | 1.25 | 0 | Section headers |
| h3 | Plex Sans Condensed | Medium 500 | 1.125rem / 18px | 1.35 | 0 | Card, table, and panel titles |
| body-prose | Source Serif 4 | Regular 400 | 1.0625rem / 17px | 1.65 | 0 | Architecture write-up, methodology prose |
| body-ui | Plex Sans Condensed | Regular 400 | 0.9375rem / 15px | 1.45 | +0.005em | Buttons, nav, form labels, non-numeric table cells |
| caption | Plex Sans Condensed | Regular 400 | 0.8125rem / 13px | 1.4 | +0.01em | Timestamps, provenance lines, status subtext |
| mono-data | Plex Mono | Regular 400 | 0.9375rem / 15px | 1.5 | 0 | SQL blocks |
| mono-table | Plex Mono | Regular 400 | 0.8125rem / 13px | 1.45 | 0 | Numeric table cells, trace IDs, coordinates |

Headings are set in sentence case, never all-caps, and never letter-spaced beyond the `body-ui`/`caption` values above — this is a deliberate rejection of the tracked-caps "eyebrow label" pattern (Pass 2, item 4). The one place uppercase appears at all is short, fixed UI chrome (e.g., a status chip's word "LIVE") at `caption` size and weight, never stretched across a whole line above a heading.

Only the weights actually specified above ship — not the full Plex superfamily — to keep font-loading weight down for the "fast on a mid-range phone" requirement in `docs/build-plan.md` §5.19; this is flagged again as a resourcing note in Open Questions.

---

## 4. Layout — wireframes

Base grid (desktop): 12 columns, 1120px max content width, 24px gutter, 16px minimum side margin below 1120px. A persistent header (wordmark, four nav links, GitHub link) appears on all five routes and is not redrawn in every wireframe below. All numbers shown are illustrative placeholders (see the note at the top of this document).

### `/` — landing

**Desktop (≥1120px)**

```
┌────────────────────────────────────────────────────────────────────────┐
│ GTA HOUSING PIPELINE          Ask   Dashboard   Evals   Architecture   GitHub │
├────────────────────────────────────────────────────────────────────────┤
│  cols 1–7                              cols 8–12                       │
│  ┌─────────────────────────────┐  ┌───────────────────────────────┐  │
│  │ H1                            │  │ SYSTEM STATUS                  │  │
│  │ "This pipeline ingests four   │  │ ● Live                          │  │
│  │  GTA municipal open-data      │  │   4 of 4 sources                │  │
│  │  feeds into one queryable     │  │                                  │  │
│  │  model, and answers plain-    │  │ Last refresh                    │  │
│  │  English questions against    │  │   2026-09-08, 04:12 America/    │  │
│  │  it — grounded, cited, and    │  │   Toronto                       │  │
│  │  scored."                     │  │                                  │  │
│  │                                │  │ Permits issued (gold layer)     │  │
│  │                                │  │   41,208                        │  │
│  │                                │  │ Applications tracked            │  │
│  │                                │  │   12,904                        │  │
│  │                                │  │ [ Ask a question ]  [ Repo ]    │  │
│  └─────────────────────────────┘  └───────────────────────────────┘  │
│                                                                          │
│  cols 1–12 — data table, real semantics (§5)                           │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ PIPELINE STATUS — per source                                    │  │
│  │ Source          Last ingested         Rows      Status          │  │
│  │ Toronto CKAN    2026-09-08 04:02      18,442    ● Live          │  │
│  │ Mississauga     2026-09-08 04:04       9,110    ● Live          │  │
│  │ Brampton        2026-09-07 22:40       7,881    ● Live          │  │
│  │ Peel            2026-09-01 03:00       5,775    ▲ Stale (7d)    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  cols 1–12 — the one bold element (§8)                                 │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  GTA municipal boundaries, filled by permits issued in the       │  │
│  │  trailing 12 months (Permit Gold scale). Static SVG, no pan/zoom,│  │
│  │  bound to the same gold-layer figures as the table above it.     │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Footer: repo · licence · sources · attribution                        │
└────────────────────────────────────────────────────────────────────────┘
```

Eye lands first on the H1 sentence (top-left, largest text on the page other than metric numerals) then moves right to the status panel in the same first screen — the two-sentence claim and the live proof sit side by side deliberately, so neither is read without the other.

**380px**

```
┌──────────────────────────┐
│ GTA HOUSING PIPELINE   ☰ │  ← wordmark + repo icon + nav toggle, one row
├──────────────────────────┤
│ H1 (2 sentences,          │
│  Plex Sans Cond, 32px)    │  ── above the fold ──
│                            │
│ ● Live — 4 of 4 sources    │
│ Last refresh: 2026-09-08   │
│  04:12 ET                  │
│ [ Ask a question ]         │
│ [ View repo ]              │
├──────────────────────────┤  ── fold, roughly here on a 700px-tall phone ──
│ PIPELINE STATUS            │
│ (per-source rows, stacked  │
│  as label:value pairs, not │
│  a squeezed 4-col table)   │
│  Toronto CKAN               │
│   18,442 rows · Live        │
│   (fix: two lines, no dot,  │
│    see component rule §5)   │
├──────────────────────────┤
│ MAP (below the fold —      │
│  supporting evidence, not  │
│  the proof itself)          │
├──────────────────────────┤
│ Footer links                │
└──────────────────────────┘
```

The compact status line (live/dead count, last refresh, links to ask + repo) is the one thing guaranteed above the fold at 380px — that line, plus the two-sentence H1, is what the ninety-second test actually checks, so the map and the full per-source table are allowed to sit below the scroll.

### `/ask` — the query console

This route carries the hardest constraint in the brief: answer, rows, SQL, and trace link all visible at once, with no toggle, on both a wide screen and a 380px phone.

**Desktop (≥1120px)** — a sticky two-column split solves it: the left column scrolls with the answer and the (potentially long) rows table; the right column stays pinned so the SQL and trace are visible no matter how far the rows table scrolls.

```
┌────────────────────────────────────────────────────────────────────────┐
│ Header                                                                    │
├────────────────────────────────────────────────────────────────────────┤
│ ASK THE WAREHOUSE                                                        │
│ ┌──────────────────────────────────────────────────────────────────┐  │
│ │ [ question textarea, full 1120px width ]                          │  │
│ │ [ Ask ]                                                             │  │
│ └──────────────────────────────────────────────────────────────────┘  │
│ Try:  [Units approved in Mississauga, 2023]                             │
│       [Which Toronto wards have the most mixed-use applications?]       │
│       [What will condo prices be in 2027? — the system refuses this]    │
│                                                                          │
│  cols 1–8 (scrolls)                       cols 9–12 (sticky)           │
│  ┌───────────────────────────────┐  ┌───────────────────────────┐    │
│  │ ANSWER                         │  │ SQL EXECUTED                │    │
│  │ [streamed prose answer,        │  │ SELECT municipality,        │    │
│  │  Source Serif]                 │  │   COUNT(*) AS permits       │    │
│  │                                 │  │ FROM fct_permits            │    │
│  │                                 │  │ WHERE ...                   │    │
│  ├───────────────────────────────┤  │                    [ Copy ]  │    │
│  │ RETRIEVED ROWS (127)            │  ├───────────────────────────┤    │
│  │ municipality  year   permits   │  │ TRACE                       │    │
│  │ Mississauga   2023    3,204    │  │ trace_id 7f2a19e             │    │
│  │ Toronto       2023   11,890    │  │ [ Open full trace ]          │    │
│  │ ...                             │  ├───────────────────────────┤    │
│  │ showing 20 of 127 rows          │  │ LATENCY                     │    │
│  └───────────────────────────────┘  │   1.8s                       │    │
│                                      ├───────────────────────────┤    │
│                                      │ COST                         │    │
│                                      │   $0.004                     │    │
│                                      └───────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────┘
```

**380px** — the wide-rows-table-on-a-narrow-screen problem is solved here, not deferred: the rows table sits inside its own bordered, horizontally-scrollable region with a fixed caption stating exactly how many columns and rows it holds, so a screen-reader user or a sighted user both learn there's more without relying on a scrollbar or a fade gradient alone. Everything is stacked, in reading order, and nothing is behind a tab — a phone visitor scrolls to see all four things, which satisfies "visible, not behind a toggle" without requiring four panels to fit one screen at once.

```
┌──────────────────────────┐
│ GTA HOUSING PIPELINE   ☰ │
├──────────────────────────┤
│ [ question textarea ]      │
│ [ Ask ]                    │
│ Try:                       │
│  [chip] [chip]             │
│  [chip — the refusal case] │
├──────────────────────────┤
│ ANSWER                     │
│ [streamed prose]            │
├──────────────────────────┤
│ RETRIEVED ROWS (127)        │
│ ┌────────────────────────┐│
│ │ muni.  year  permits   ││  ← bordered, horizontally
│ │ Missi… 2023   3,204    ││    scrollable; 3 of 3
│ │ Toron… 2023  11,890    ││    columns shown, none cut
│ └────────────────────────┘│
│ 3 columns, 20 of 127 rows,  │
│ scroll horizontally          │
├──────────────────────────┤
│ SQL EXECUTED                │
│ [mono block, soft-wrapped,  │
│  full statement, no scroll  │
│  needed — SQL wraps on      │
│  indentation]                │
│ [ Copy ]                     │
├──────────────────────────┤
│ Trace: trace_id 7f2a19e      │
│ [ Open full trace ]           │
├──────────────────────────┤
│ Latency: 1.8s                │
│ Cost: $0.004                 │
└──────────────────────────┘
```

A card-per-row redesign for the mobile rows table was considered and rejected: turning each row into a stacked key-value card hides the ability to compare one column down the page, which is the entire point of showing retrieved rows as evidence. A bounded, captioned, horizontally-scrollable table keeps the real tabular relationship intact.

### `/dashboard` — Power BI embed

**Desktop**

```
┌────────────────────────────────────────────────────────────────────────┐
│ Header                                                                    │
├────────────────────────────────────────────────────────────────────────┤
│ DASHBOARD                                                                 │
│ One sentence: what this report covers and how often it refreshes.       │
│                                                                          │
│  cols 1–9                                    cols 10–12                │
│  ┌─────────────────────────────────┐  ┌───────────────────────────┐  │
│  │ "drawing-sheet" frame:            │  │ WHAT EACH PAGE ANSWERS      │  │
│  │ ┌───────────────────────────────┐│  │ 1. GTA Overview              │  │
│  │ │ title strip: "Power BI report" ││  │    Units and permits, this   │  │
│  │ │ [ embedded report iframe ]     ││  │    year vs prior             │  │
│  │ │                                 ││  │ 2. Municipal Comparison       │  │
│  │ │                                 ││  │    Who is building, per      │  │
│  │ └───────────────────────────────┘│  │    capita and per hectare     │  │
│  └─────────────────────────────────┘  │ 3. Pipeline Velocity          │  │
│                                        │    Application to permit time │  │
│                                        │ 4. Geography                  │  │
│                                        │    By ward and census tract   │  │
│                                        │ 5. Data Quality & Freshness   │  │
│                                        │    Gaps, stated plainly       │  │
│                                        │                                │  │
│                                        │ Last refresh: 2026-09-08       │  │
│                                        │ Data dictionary (link)          │  │
│                                        └───────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

The report sits inside a bordered frame with its own title strip — a deliberate echo of a drawing's title block — so the visual seam between "our site" and "an embedded third-party iframe with its own theme" is framed on purpose rather than hidden. See Open Questions for the limits of what this framing can and can't fix.

**380px** — the plain-language notes come first, before the heavy iframe, so a phone visitor gets the answer to "what does this dashboard show" even if they never scroll to the embed itself:

```
┌──────────────────────────┐
│ Header                     │
├──────────────────────────┤
│ DASHBOARD framing sentence  │
├──────────────────────────┤
│ WHAT EACH PAGE ANSWERS       │
│ 1. GTA Overview               │
│ 2. Municipal Comparison        │
│ 3. Pipeline Velocity            │
│ 4. Geography                     │
│ 5. Data Quality & Freshness       │
│ Last refresh: 2026-09-08            │
├──────────────────────────┤
│ [ embedded report frame,      │
│   full width ]                  │
│ Best viewed on a larger screen  │
│ — pinch to zoom.                  │
│ Open the report on its own page  │
└──────────────────────────┘
```

### `/evals` — the scorecard

**Desktop**

```
┌────────────────────────────────────────────────────────────────────────┐
│ Header                                                                    │
├────────────────────────────────────────────────────────────────────────┤
│ EVALS — how we know it works                                             │
│ One-paragraph plain-language framing.                                   │
│                                                                          │
│  6 metric tiles, one per bucket, 6 columns                              │
│  ┌───────┬───────┬───────┬───────┬───────┬───────┐                    │
│  │Simple │Compar-│Tempor-│Geo-   │Seman- │Refusal│                    │
│  │aggre- │ative  │al/    │graphic│tic/   │accur- │                    │
│  │gate   │       │trend  │       │text   │acy    │                    │
│  │ 92%   │ 81%   │ 78%   │ 85%   │ 74%   │ 95%   │                    │
│  │▲ +3pt │▼ -4pt │  —    │▲ +1pt │▼ -6pt │  —    │                    │
│  └───────┴───────┴───────┴───────┴───────┴───────┘                    │
│                                                                          │
│  cols 1–12                                                               │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ SCORE HISTORY — every CI run, including the ones that went down  │  │
│  │  100%┤                                                            │  │
│  │      │  refusal accuracy (— — dashed line, labelled at line end)  │  │
│  │   80%┤ solid line ‾\_‾\___    ...dotted line semantic/text        │  │
│  │      │              ▼ run a1b2c3, 2026-08-30                     │  │
│  │   60%┤                 semantic/text dropped 80% → 74%           │  │
│  │      └──────────────────────────────────────────────            │  │
│  │        run1   run2   run3   run4   run5   run6 (latest)         │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Methodology (prose) + full per-question breakdown table (mono numbers) │
└────────────────────────────────────────────────────────────────────────┘
```

**380px** — six-series line charts do not survive compression to 380px legibly; rather than shrink one dense chart, each bucket gets its own labelled sparkline, stacked:

```
┌──────────────────────────┐
│ Header                     │
├──────────────────────────┤
│ EVALS framing paragraph     │
├──────────────────────────┤
│ Simple aggregate   92%  ▲3  │  ← 6 tiles, full-width rows,
│ Comparative        81%  ▼4  │    stacked, not compressed 2-up
│ Temporal/trend     78%   —  │
│ Geographic         85%  ▲1  │
│ Semantic/text      74%  ▼6  │
│ Refusal accuracy   95%   —  │
├──────────────────────────┤
│ SCORE HISTORY                │
│ Simple aggregate               │
│  [sparkline] latest 92%        │
│ Comparative                     │
│  [sparkline] latest 81%         │
│ ...one sparkline per bucket,     │
│ each with its own regression      │
│ marker and caption below it        │
├──────────────────────────┤
│ Methodology (prose)                │
│ Full table (horizontal scroll,      │
│ same treatment as /ask rows table)   │
└──────────────────────────┘
```

### `/architecture` — the write-up

**Desktop** — the one route where prose readability overrides the site-wide 1120px grid: the diagram breaks to the full container width, but the prose column narrows to ~720px for line-length, with a sticky table of contents alongside it.

```
┌────────────────────────────────────────────────────────────────────────┐
│ Header                                                                    │
├────────────────────────────────────────────────────────────────────────┤
│ ARCHITECTURE                                                              │
│  cols 1–12 — diagram at full container width                            │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ Sources → Bronze → Silver → Gold → Serving/AI/Eval → Web App      │  │
│  │ (the box diagram from docs/build-plan.md §2, rendered as a real   │  │
│  │  graphic, not a screenshot of the ASCII)                           │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  cols 2–8 (≈720px prose)                    cols 9–11 (sticky)         │
│  ┌─────────────────────────────┐      ┌───────────────────────┐      │
│  │ Prose, Source Serif, 17px,   │      │ ON THIS PAGE            │      │
│  │ 1.65 line-height.            │      │ Sources                 │      │
│  │ Inline citations to ADRs     │      │ Bronze/Silver/Gold      │      │
│  │ appear as plain text links   │      │ AI query layer          │      │
│  │ within the paragraph, e.g.   │      │ Eval harness             │      │
│  │ "(see ADR-0007)".            │      │ Decision records          │      │
│  │                               │      │ (jumps to each H2)         │      │
│  └─────────────────────────────┘      └───────────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
```

**380px** — TOC becomes a static list above the prose, not a floating element that eats screen space; the diagram is redrawn as a vertical stack of stages, not a shrunk version of the wide one:

```
┌──────────────────────────┐
│ Header                     │
├──────────────────────────┤
│ ARCHITECTURE                │
│ On this page: Sources,       │
│ Bronze/Silver/Gold, AI query  │
│ layer, Eval harness,           │
│ Decision records                │
├──────────────────────────┤
│ [ vertical diagram: 6         │
│   stacked boxes, Sources        │
│   at top, Web App at bottom ]     │
├──────────────────────────┤
│ Prose, full width, single         │
│ column                              │
└──────────────────────────┘
```

---

## 5. Components

Global rule applying to every component below: **flat surfaces, no shadow, no rounded-card treatment.** Corners are sharp or barely rounded (0–2px — a drafted rectangle, not an app-icon card). Borders (Ink at reduced strength, from §2) do all the separating work a shadow would otherwise fake.

**Status indicator** — Purpose: communicate live/stale/dead per-source or overall system health. States: *Live* (Parcel Green dot + word "Live," second line "updated 2h ago"), *Stale* (Permit Gold Fill dot + "Stale," second line "7d since refresh — exceeds 2x cadence"), *Down* (Register Red dot + "Down," second line "last seen 9d ago"), *Not yet measured* (hollow Ink-secondary outline dot + the literal words "Not yet measured" — this state exists because the truth-discipline rule in §4 of the build plan requires it during early phases, not as a fallback to hide behind later). Rule: colour is never the only signal — dot and word always travel together, on two lines, never joined by a middle dot or any punctuation glue. Always sourced from the manifest or `/status`; never hand-written.

**Data table** — Purpose: render real row-level data (retrieved rows, per-source health, eval breakdown) with full HTML table semantics. States: populated, empty (zero rows returned — a distinct message from "not yet run"), overflow (bordered horizontal-scroll container with an explicit caption stating column and row counts, per the `/ask` wireframe above), truncated ("showing 20 of 127 rows"). Rule: numeric columns are right-aligned in `mono-table`; a `<caption>` names what the table is and how many rows it holds; used only for genuine row-level data, never as a layout device.

**Code/SQL block** — Purpose: show the exact executed SQL, in full, always. States: default (a slightly recessed surface — the same surface hue at reduced opacity, never a shadow), copied (inline text "Copied" appears next to the button for two seconds, no animated toast). Rule: no colour-coded syntax highlighting — keywords get a weight change (Medium vs. Regular), not a rainbow theme; a flashy IDE-style highlighter reads as a marketing flourish, not a read-only artifact. Never truncated with a "show more" — the whole statement renders, wrapped on its own indentation if needed.

**Metric tile** — Purpose: a single number as evidence (row counts, latency, cost, eval bucket score). States: value present (`display-metric` numeral + `caption` label + optional delta), not yet measured (the literal words "not yet measured" in place of the numeral — never a zero, dash used as a value, or fabricated placeholder), loading. Rule: numeral always in Plex Mono so a row of tiles aligns on the baseline; a delta is a real glyph (▲/▼) plus a plain-text sign (+3pt / -4pt), never colour alone.

**Chart frame** — Purpose: the container for the eval history chart, dashboard mini-notes, and the map. Every chart frame carries a fixed 1px Ink-strength border and a visible caption line beneath it stating the data source and as-of date ("Source: `evals/results/2026-09-08-a1b2c3.json`") — no chart ships without a provenance line, mirroring the rule that every number in the README traces to a committed file. Axis labels in `caption` (Plex Sans Condensed); tick values in `mono-table`.

**Empty state** — Purpose: the first-class rendering required whenever real data legitimately doesn't exist. This is not a decorative illustration — no mascot, no line-drawing graphic. It is a thin dashed rule where the value would sit, plus one sentence naming the specific reason, drawn from a fixed, small vocabulary so it is always accurate rather than generically reassuring:
- *not-yet-run* — "This has not been ingested/evaluated/deployed yet. See `docs/build-plan.md` Phase N."
- *zero-results* — "No rows matched this question." (distinct from a system error)
- *source-down* — "This source hasn't refreshed within 2x its declared cadence. See `docs/sources/{name}.md`."
- *awaiting-data* — "Retrieval succeeded but no eval run has scored this bucket yet."
Rule: an empty state must actually be triggered by absent data, never designed and left unused — during Phases 1 through 3, most of the site legitimately renders these, and that's the point, not a bug to hide.

**Error state** — Purpose: a failed request (API down, timeout, malformed input, rate limit, spend ceiling). Register Red is used here and only here as a background/border accent (never as the badge for every warning). Message states what happened and what the visitor can do next (retry / read the status note / see a cached example) — never a raw stack trace. The spend-ceiling case is explicitly *not* styled as an error: it uses the neutral Ink-secondary tone with the message "Daily query budget reached — showing a cached example answer instead," because that is the API's rate limiter working correctly (per `docs/build-plan.md` §5.20/R10), and painting a working safety mechanism red would misrepresent it as a bug.

**Loading state** — Purpose: the `/ask` wait, a chart data fetch, the dashboard iframe load. No spinner (forbidden explicitly in the build plan). See §6 — this is the site's one motion moment.

---

## 6. Motion and interaction

**One deliberate motion moment: the plotter line.** During a live `/ask` query, a thin 2px rule in Survey Blue draws left-to-right beneath the question box while the real pipeline stage streams in as text underneath it — "Planning query…" → "Executing SQL…" → "Checking answer…" — sourced from the actual planner/executor/critic trace events as they arrive, not a decorative timer. It is named for what it resembles: a pen plotter drawing a line, the literal device that once produced these technical drawings. This is the only place on the site where something genuinely happens asynchronously over a few seconds of visible duration, so it is the only place motion earns its keep. Everywhere else, state changes instantly — data is either there or it renders its empty state; there is no fade-in, no hover-lift, no scroll-triggered reveal, and no animated counter ticking a number up on load.

`prefers-reduced-motion: reduce` — the plotter line's sweep is replaced by a static three-item step list (Planning / Executing / Checking) where each step gets a solid checkmark the instant it completes, no animation, no opacity transition, same information conveyed by state alone.

**Focus states** — every interactive element (nav links, example chips, the Ask button, the copy button, the horizontal-scroll table region, chart legend items if interactive) gets a solid 2px outline in Survey Blue (light) or Ice Blue (dark), offset 2px from the element, never `outline: none`. Both ring colours were confirmed above at 7.94:1 and 8.28:1 against their backgrounds — far past the 3:1 non-text minimum. A solid outline is used rather than a soft glow/shadow, because a glow can fail to render visibly on some displays and is one step from the soft-shadow-card cluster this plan is already avoiding.

---

## 7. Accessibility floor

**Contrast** — every pair in §2 clears 4.5:1 for body text or 3:1 for large text/UI boundaries, computed (not eyeballed) from the WCAG relative-luminance formula. The one pair with no headroom to spare is Register Red Dark on Blueprint at 4.81:1 — it must not be reused smaller or lighter than the `caption`/`body-ui` sizes specified in §3.

**Focus indicators** — specified in §6; visible, solid, 2px, offset, never removed.

**Keyboard path through `/ask`** — skip-to-content link (visually hidden until focused) → nav → question textarea → example chips (real `<button>` elements, standard tab order, not a custom widget requiring arrow-key navigation) → Ask button → on response: answer region (a heading landmark, not itself focusable) → rows table (normal document flow; if horizontally scrollable, the scroll container carries `tabindex="0"` and an `aria-label` stating it's scrollable) → SQL block's copy button → trace link → new-question control. DOM order matches this list regardless of the two-column visual arrangement at desktop — the sticky right rail is placed via CSS, not by reordering the DOM, so keyboard and screen-reader order stay sane independent of layout.

**Table semantics** — every data table gets a `<caption>` stating what it is and its row count, `<th scope="col">` on every column header, no merged or spanning cells (kept simple and robust rather than clever), numeric alignment done in CSS rather than inserted whitespace. If a column is sortable, the control is a real `<button>` inside the `<th>` with `aria-sort` reflecting current state.

**Eval history chart, colour-independent** — each bucket's line gets a distinct dash pattern (solid / dashed / dotted / dash-dot) plus a direct end-of-line text label, not a colour-only legend swatch. Every regression point carries a shape marker (▼) and a text caption beneath the chart naming the run, the date, and the exact before/after numbers — so the information exists in text regardless of how the chart itself renders. The same numbers are always also rendered in a plain data table directly below the chart; the chart illustrates the table, it never replaces it.

**Target: Lighthouse accessibility ≥ 95.** The categories most likely to cost points if this plan is under-implemented: colour contrast (covered above, with no margin to spare on one pair), name/role/value on the custom chips and copy button (must be real `<button>` elements with accessible names, not styled `<div>`s), list semantics on the example-question set, and one landmark region set per route (`<header>`, `<nav>`, `<main>`, `<footer>`) so a screen-reader user can jump between them. Checked in CI per `.github/workflows/web.yml`.

---

## 8. Where the boldness is spent

**The GTA municipality map on the landing page.** It is the one place on the site with real colour saturation, real shape variety, and something close to visual weight — everywhere else (tables, tiles, buttons, chips, the SQL block) is flat, bordered, and quiet on purpose. The map is a static SVG of the four municipal boundaries (Toronto, Mississauga, Brampton, Peel), filled using the Permit Gold scale from §2, bound directly to the same gold-layer permit-volume figures shown in the status table beside it — no pan, no zoom, no ward-level drill-through, no external map-tile service. It earns the site's one moment of visual richness because it is real geography carrying real numbers, and for an audience of hiring managers evaluating a data platform, that is a more persuasive signal than any typographic or decorative flourish could be — and because it reuses the palette's own zoning-legend logic rather than introducing new decoration, the boldness and the restraint rule are the same design decision, not two competing ones.

---

## Pass 2 — self-critique

Checked Pass 1 against each item in the generic-AI-design cluster. Two items required real changes; the rest were checked and confirmed absent, with the reasoning for each written out below (not skipped).

**1. Cream background + high-contrast serif + terracotta accent — changed.** The first pass at this palette, working from "municipal planning documents" as the brief, reached almost exactly for this cluster: a warm parchment background, a serif for headings, a warm reddish accent. Caught and revised three ways: (a) the light background moved from a cream/parchment tone to a cooler, less nostalgic bond-paper white (`#F6F5F0`) that reads as a technical printout, not an aged document; (b) headings use no serif at all — Source Serif 4 is reserved for long-form body prose only, never a headline, and it was chosen specifically for *low* stroke contrast, the opposite of the flagged pattern; (c) the accent is not terracotta — Register Red is a muted stamp-ink red used only for two semantic meanings (refusal, error), never as a decorative accent on buttons or icons generally, which is a much narrower footprint than a terracotta accent typically gets.

**2. Near-black background + one acid accent — checked, not present.** Dark mode's background is a genuine blue (`#10233A`, Blueprint) with clearly non-neutral hue, not a desaturated near-black. The system uses four distinct accent hues tied to four distinct meanings (refusal, success, link, data), not one glowing accent colour standing in for everything.

**3. Identical rounded cards with the same soft grey shadow — changed.** This wasn't explicit in the first draft of the Components section; metric tiles, chart frames, and panels were sketched without a stated corner/shadow rule, which is exactly how this pattern sneaks in during implementation even when nobody intends it. Fixed by adding the global rule at the top of §5: no shadow anywhere on the site, corners sharp or 0–2px, borders do the separating work instead.

**4. ALL-CAPS tracked eyebrow labels above every heading — checked, not present.** Headings are sentence case at zero extra letter-spacing (§3); the only uppercase text on the site is short, fixed status-chip words like "LIVE," set at `caption` size, never stretched across a line above a heading as a recurring pre-headline tag.

**5. Meta information joined with middle dots — changed.** The build plan's own prose (and my first pass at this document) reaches for middot joins constantly — "Owner: X · Date: Y," "Live · updated 2h ago." Caught it in the status-indicator copy and in three of the wireframes (the landing page's stat panel, the dashboard's title strip, an `/ask` metrics box) and rewrote every instance as either two stacked lines or a labelled row, never a punctuation-glued string. This is called out specifically because it's easy to miss — it's not in the interface yet, only in draft copy, but draft copy is exactly where this habit ships into a component if nobody catches it here.

**6. An arrow character appended to link text — changed.** The first draft of the landing page used a down-arrow ("See full pipeline status ↓") as an in-page jump link. Removed by restructuring the page so the summary panel sits directly beside the detail table instead of requiring a jump — the fix here wasn't "delete the arrow," it was "delete the need for the link." No link on the site carries a trailing arrow glyph of any kind.

**7. Numbered `01 / 02 / 03` markers on content that isn't a sequence — checked, not present, with one deliberate exception.** No bucket, tile, or category anywhere on the site gets an arbitrary ordinal badge — the six eval buckets are labelled by name, not numbered. The one place numbers do appear next to list items is the Power BI report's five pages on `/dashboard` ("1. GTA Overview" … "5. Data Quality & Freshness") — and that's a legitimate exception, not a slip: those five pages are a genuinely ordered set defined in `docs/build-plan.md` §5.16, built and navigated in that order inside the actual report.

### Would this read as "another Next.js portfolio app"? (R11)

No, on the plan as specified: there is no hero photograph or illustration, no gradient-mesh background, no oversized rounded call-to-action button, and no marketing copy anywhere in the wireframes — the landing page leads with a live status panel and real row counts before any typographic flourish, and the palette derives from a real municipal document tradition rather than a design-tool default. The residual risk is not in this plan, it's in implementation: if `frontend-engineer` reaches for a component library's defaults (shadcn/ui's default card shadow and radius, Tailwind's default blue-600 link colour, a default sans stack) rather than deliberately overriding them to match §2–§5, the site drifts back toward generic regardless of what's written here. That risk is named explicitly in Open Questions below as an instruction for Phase 4b, not left implicit.

### Is there anything here disproportionate to what it proves? (R12)

Yes — three things were deliberately cut or kept minimal for exactly this reason, rather than left to be discovered as overruns mid-build:

- **The map is static, not an interactive GIS layer.** A hover-tooltip, pan/zoom, ward-level drill-through map would need boundary GeoJSON, a mapping library, and real interaction design and testing — expensive, for a component whose whole job is "prove real geography, real numbers" at a glance. A static SVG bound to the same figures as the adjacent table proves the same thing for a fraction of the build time.
- **No custom syntax highlighter for SQL.** A full CodeMirror/Prism integration buys visual polish the brief doesn't ask for; a monospace block with keyword weight change is enough to read the query and far cheaper to build and maintain.
- **No heavyweight charting library for `/evals`.** The history chart needs direct labels, dash patterns, and regression markers, not zoom, pan, or crosshair tooltips across series — a small hand-built SVG line chart (or the lightest library that can produce one) is proportionate; a full dashboarding chart library is not.

---

## Open questions for the Director

1. **Power BI embed theming.** An embedded report brings its own fonts, colours, and control chrome that this plan does not fully control. The plan's fallback is the "drawing-sheet" frame in the `/dashboard` wireframe (§4) — a bordered, titled container that makes the seam deliberate rather than hidden. The better fix is a custom Power BI report theme (JSON) approximating Surface/Ink/the accent hues, built during Phase 3 by `semantic-model-designer`/`report-builder`. Please confirm whether a custom PBI theme is in scope and budget for Phase 3, or whether the framed-embed-only fallback is the accepted answer for Gate 4b.
2. **Subdomain.** This plan refers throughout to "the proposed target" and never hardcodes a URL, per the header note in `docs/build-plan.md`. Confirm the final subdomain before any component embeds a literal URL.
3. **Eval bucket count.** The `/evals` layout (§4) is built around exactly six bucket tiles and six sparklines at 380px. Confirm the six buckets in `docs/build-plan.md` §5.13 are final before `frontend-engineer` hard-codes that grid — a seventh bucket breaks the math.
4. **Map data availability.** The landing-page map (§8) needs permit volume by municipality for the trailing 12 months from the gold layer. Confirm the exact field/view this binds to, and confirm it will exist by the time Phase 4b starts (weeks 6–7) — if it slips, the map has no real data to render and should fall back to the per-source table alone rather than shipping with a placeholder.
5. **Municipal boundary geometry.** Confirm a licensed, reusable GeoJSON (or equivalent) for Toronto/Mississauga/Brampton/Peel boundaries is available. If boundary data can't be confirmed as licensable in time, the fallback is a non-geographic four-panel comparison grid instead of a literal map — decide now so this doesn't surface as a late R12 scramble.
6. **Font bundle size.** IBM Plex Sans Condensed, Source Serif 4, and IBM Plex Mono are all OFL-licensed and free to self-host, but only the specific weights listed in §3 should ship, not the full superfamilies — flagging for sign-off since font weight is a real, measurable cost against the "fast on a mid-range phone" requirement.
7. **Dark mode sequencing.** Confirm whether dark mode must ship for Gate 4b or can follow shortly after light mode ships, given the timebox in R12 — the palette and contrast work above already covers both, so this is a sequencing question, not a design one.
