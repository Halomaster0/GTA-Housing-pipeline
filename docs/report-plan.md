# Report plan — Power BI, five pages (build spec for `report-builder`)

Owner: `report-builder`, reviewed by `director-analytics` against the
checklist in build-plan §5.14. Every visual names its measure from
`docs/data-dictionary.md` (M1–M8, P1–P3); every headline number must match
`docs/measure-reconciliation.json` or the page is wrong. No visual may show
a pending measure (P1–P3) as zero — explicit empty states only.

Slicers (global): municipality, year (dim_date), use type. Cross-filtering
deliberate: slicers filter facts; drilling a ward filters only the
geography visuals (Toronto/Brampton permits have no ward — a ward drill
that silently dropped 793,305 permits would be a lie; the geography page
states its denominator).

## Page 1 — GTA Overview (M1, M2, M3)

Job: is the region building, and where. Cards: permits issued (M1, latest
complete year vs prior), net new units (M2, basis-tagged), active
applications (M3). Bar: permits issued by municipality × year (M1 year
table). Donut: application status mix (M5). Latest complete year in data:
2025 (2026 partial — label it partial, don't annualise).

## Page 2 — Municipal Comparison (M1, M2 + P1 empty state)

Job: who is actually building. Same measures normalised — except
per-capita (P1) is an explicit empty state: "per-capita pending StatCan
census profiles" with the reconciliation reference. Until P1 lands, the
page compares raw volumes + status mixes only, and says so in a subtitle.
Caledon card: explicit no-data state per the approved design condition
("Caledon issues no permits in these feeds — in scope as geography",
ADR-0004), never a zero.

## Page 3 — Pipeline Velocity (M6, M7 + P2 empty state)

Job: how long things take. Histograms: applied→issued days by municipality
(M6: TOR 28d / MISS 34d / BRAM 44d medians, coverage n stated).
Submitted→decision (M7): Mississauga only (385d median, n=1,163) —
Toronto/Brampton panels are empty states ("no decision dates in source"),
not omissions. Application→permit timing (P2) is an empty state citing
ADR-0006. This page is where the honesty shows; do not smooth it.

## Page 4 — Geography (M1 by ward where valid)

Job: where inside each municipality. Map by ward for Mississauga
applications + permits and Toronto applications (ward-attributed rows
only). Brampton ward view carries the UNCONFIRMED-equivalence caveat
(matrix §3) as a visible footnote. Toronto permits are NOT on this map
(grid-ref, not wards) — the page states its denominator (34,614 + 8,601 +
attributed rows) so no one mistakes it for the 827,919-permit universe.

## Page 5 — Data Quality & Freshness (mandatory, not optional)

Job: prove the numbers. Last refresh (ingest_batch_id / manifest date),
per-source row counts (bronze manifest totals), gold totals (827,919 /
21,658), orphan-FK counts (0 / 0), NULL-geography and UNKNOWN-use counts
with one-line reasons each, unit-basis banner (ADR-0003), pending-measure
list (P1–P3 with owners). This page is generated from
`measure-reconciliation.json` + `data-quality-report.md`, not hand-typed.
A reader who only opens this page should still trust the other four.
