# Fabric DAX measure library (M1–M8)

Owner: `semantic-model-designer`. Each measure below mirrors its
`docs/data-dictionary.md` definition 1:1 — the DuckDB SQL there is verified
against the warehouse, the DAX here is its translation. **After the first
provisioned refresh, every value must be read off the model and compared to
`docs/measure-reconciliation.json` before the report publishes.** A mismatch
means the model is wrong, never the JSON.

## Relationships (set once, single filter direction everywhere)

- `fct_permits` / `fct_applications` → `dim_municipality`, `dim_use_type`,
  `dim_status`, `dim_geography`: many-to-one, single direction.
- Date roles (only ONE active per fact or results double-count):
  - `fct_permits[date_issued_sk]` → `dim_date[date_sk]` **active**.
    `date_applied_sk`, `date_closed_sk` inactive — activate per-measure with
    `USERELATIONSHIP`.
  - `fct_applications[date_submitted_sk]` → `dim_date[date_sk]` **active**.
    `date_decision_sk` inactive — same treatment.
- Mark `dim_date` as the date table on `calendar_date`.

## Measures

```dax
/* M1 — Permits issued (has an issue date; status-agnostic by definition) */
Permits Issued =
CALCULATE (
    COUNTROWS ( fct_permits ),
    NOT ( ISBLANK ( fct_permits[date_issued_sk] ) )
)

/* M2 — Net new units. NULLs excluded by SUM semantics. Basis 'unknown':
   add a card visual stating cross-municipality sums are NOT comparable. */
Net New Units = SUM ( fct_permits[unit_count_net_new] )

/* M3 — Active applications (non-terminal status; APPEALED counts as active) */
Active Applications =
CALCULATE (
    COUNTROWS ( fct_applications ),
    dim_status[is_terminal] = FALSE ()
)

/* M4/M5 — Status mixes need no measures: COUNTROWS sliced by dim_status.
   Reference values in reconciliation JSON (permits/applications by
   municipality × status tables). */

/* M6 — Median applied→issued days (permits having both dates only) */
Median Applied to Issued Days =
MEDIANX (
    FILTER (
        fct_permits,
        NOT ( ISBLANK ( fct_permits[date_applied_sk] ) )
            && NOT ( ISBLANK ( fct_permits[date_issued_sk] ) )
    ),
    DATEDIFF (
        RELATED ( AppliedDate[calendar_date] ),
        RELATED ( IssuedDate[calendar_date] ),
        DAY
    )
)
/* Requires dim_date duplicated (or role-playing via USERELATIONSHIP) as
   AppliedDate (active on date_applied_sk) and IssuedDate. Reference:
   TOR 28d (n=460,121) · MISS 34d (n=34,581) · BRAM 44d (n=150,680). */

/* M7 — Median submitted→decision days (Mississauga only in v1) */
Median Submitted to Decision Days =
MEDIANX (
    FILTER (
        fct_applications,
        NOT ( ISBLANK ( fct_applications[date_submitted_sk] ) )
            && NOT ( ISBLANK ( fct_applications[date_decision_sk] ) )
    ),
    DATEDIFF (
        RELATED ( SubmittedDate[calendar_date] ),
        RELATED ( DecisionDate[calendar_date] ),
        DAY
    )
)
/* Reference: MISS 385d (n=1,163). Toronto/Brampton panels stay empty —
   no decision dates in source. */

/* M8 — Construction value (Brampton entirely NULL in source: page shows
   Mississauga + Toronto only, labelled) */
Construction Value CAD = SUM ( fct_permits[construction_value_cad] )
/* Reference: MISS $18.27B · TOR $100.99B. */
```

## Pending (P1–P3): no DAX until the inputs exist

Per-capita, application→permit timing, and StatCan control totals have no
measures here on purpose — defining them now would invite someone to drag
them onto a page. They get DAX when their inputs land (population,
proven key, StatCan series), per `OUTSTANDING.md` §3.
