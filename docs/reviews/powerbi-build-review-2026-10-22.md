# Power BI build review — pages 1 and 2

**Date:** 2026-10-22 · **Reviewer:** `director-analytics` + `data-quality-auditor`
**Subject:** CEO's first Power BI build (page 1 GTA Overview, page 2 Municipal
Comparison, page 3 restarted and empty)
**Evidence:** `docs/measure-reconciliation.json` (git_sha `18d4cb1`),
`docs/fabric-dax.md`, `docs/report-plan.md`, `models/gold/05_fct_permits.sql`,
ADR-0003.

---

## Verdict

**Reconciliation: PASS.** Every figure on both pages matches the committed
reconciliation output exactly — 827,919 permits; 221,319 / 34,614 / 571,986 by
municipality; 369,765 net units; 21,658 applications; the status split
(10,964 / 7,679 / 2,178 / 348) resolves to the per-municipality table row for
row. The dashboard is reading the real warehouse, not a mock.

**Publication: BLOCKED on D1 and D2 below.** Two figures are labelled as
something the data does not support. Both are on page 1, both are headline
cards, and one of them is the exact failure mode ADR-0003 exists to prevent.

---

## D1 — `Net New Units` is summed across incompatible bases (BLOCKING)

The table totals 369,765 net new units across three municipalities and prints it
in bold. `docs/measure-reconciliation.json` records the basis as:

```
"unit_basis": "unknown (ADR-0003 — cross-municipality unit sums are NOT comparable)"
```

It is worse than unknown. `models/gold/05_fct_permits.sql` lines 40–63 show the
basis is **known and mixed**:

| Municipality | Source expression | Basis |
|---|---|---|
| Toronto | `dwelling_units_created − dwelling_units_lost` | net |
| Mississauga | `res_units` | gross |
| Brampton | `dwellings` | gross |

One column named `unit_count_net_new` carrying a net value for one municipality
and gross values for two. Summing it adds a net quantity to two gross
quantities. The total is not merely uncertain — it is a category error, and
Toronto's 259,840 is understated relative to the other two by exactly the
demolitions its siblings never subtract.

ADR-0003 is explicit: *"if any contributing source row is `unknown`, the
published measure carries a comparability caveat (surfaced in the semantic model
and dashboard), **not a clean number**."* `docs/fabric-dax.md` M2 repeats it:
*"add a card visual stating cross-municipality sums are NOT comparable."*
That card is absent from both pages.

Coverage compounds it: units are NULL on **64.3%** of permit rows
(532,330 of 827,919 — Brampton 60.1%, Mississauga 80.9%, Toronto 64.9%). The
figure is a mixed-basis sum over roughly a third of the data.

**Required before publishing:** drop the Total row for Net New Units, or render
it as "not comparable — mixed basis"; add the ADR-0003 caveat card; show the
per-municipality figures with a basis tag and the NULL coverage beside them.

## D2 — `Permits Issued` is showing all permit rows, not issued permits (BLOCKING)

Measure M1 in `docs/fabric-dax.md`:

```dax
Permits Issued = CALCULATE ( COUNTROWS ( fct_permits ),
    NOT ( ISBLANK ( fct_permits[date_issued_sk] ) ) )
```

The displayed values are 221,319 / 34,614 / 571,986 / 827,919 — identical to
`permits_by_municipality` in the reconciliation JSON, which
`scripts/reconcile_measures.py:144-152` computes as a plain `COUNT(*)` with no
date filter.

Both cannot be correct. `permits_by_municipality_status` records **10,888**
permits at UNDER_REVIEW and **1,828** at APPLIED; neither state has an issue
date, so M1 must return less than 827,919.

So either the visuals are bound to a bare row count rather than M1, or M1 is
running against rows that all carry an issue date — which would be a silver-layer
defect. **One check disambiguates:** put M1 on a card beside a bare
`COUNTROWS(fct_permits)`. If they are equal, the problem is in the data, not the
report.

Overstatement is at least 12,716 (1.5%). A further **58,890** permits are
CANCELLED, which needs its own ruling: a cancelled permit was issued and then
withdrawn, so whether it counts toward "permits issued" is a definitional
decision, not an oversight. It belongs in the data dictionary either way.

**Root cause worth fixing in the harness, not just the report:**
`reconcile_measures.py` emits no M1 value, so there was nothing for the
dashboard figure to be checked against. The reconciliation file should carry
every published measure, M1 included. That is why this slipped through a
process specifically designed to catch it.

## D3 — The year chart changes composition in 2018 without saying so

`permits_issued_by_municipality_year` shows Mississauga's first year as **2018**.
Brampton and Toronto both start 2010. The stacked bar therefore shows two
municipalities for 2010–2017 and three from 2018, with no visual break.

Anyone comparing 2015 to 2022 is comparing different universes, and the jump at
2016–2017 in Toronto's series (18,597 → 32,095 → 45,690) sits right next to the
composition change, which invites exactly the wrong reading.

**Fix:** a coverage footnote naming each municipality's first year, and a
coverage-start table on page 5. Starting the cross-municipality axis at 2018
is the cleaner option if the page is about comparison rather than history.

## D4 — A donut slice has no data label

Visible labels sum to 21,311 against a centre total of 21,658. The missing 347
is REFUSED (Brampton 333 + Toronto 14), suppressed by label collision with
SUBMITTED (142).

Six categories with two slices under 2% is the wrong form. **Fix:** a sorted bar
chart, or legend-with-values and labels off.

## D5 — The dashboard is six weeks stale

The page footer reads "Data to 2026-09-10". Today is 2026-10-22. The build plan
treats a stale dashboard as worse than none, and HANDOVER-7 records refresh as
manual.

**Fix:** re-run ingest → `make export-gold` → `make reconcile`, re-upload, and
make the as-of date a measure driven by the manifest rather than typed text, so
staleness surfaces itself on page 5.

---

## Page 3 — build it, it is the strongest page in the deck

The restarted page is the one that most helps an analytics-engineering reader,
and it is fully supported by verified measures:

- **M6 applied→issued median days, all three municipalities:** Toronto 28d
  (n=460,121), Mississauga 34d (n=34,581), Brampton 44d (n=150,680). A real
  cross-municipality comparison on a basis that *is* comparable.
- **M7 submitted→decision:** Mississauga only — 385d (n=1,163). Toronto and
  Brampton render as empty states reading "no decision dates in source", per
  `report-plan.md`.
- **Application→permit timing:** empty state citing ADR-0006 — no permit↔
  application key exists in any feed.

Three honest empty states next to one solid comparison demonstrates more
judgement than a page of smoothed numbers. Do not fill them in.

---

## Two constraints to absorb before pages 4 and 5

- **Geography is Mississauga-only for permits.** `permits_null_geography` is
  793,305 of 827,919; the 34,614 remainder is exactly Mississauga's permit
  count. `report-plan.md` already scopes page 4 correctly and states its
  denominator — keep that, and do not let the map imply the 827,919 universe.
- **Use type is unknown on 94.6% of applications** (20,500 of 21,658). Any
  "mixed-use applications by ward" question is unanswerable today. This
  constrains the Geographic bucket of the Phase 4 golden question set, and
  `eval-engineer` should write those cases knowing it.
