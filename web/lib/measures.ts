import recon from "../../docs/measure-reconciliation.json";

/* Typed accessors over the committed reconciliation file (ADR-0008/0009).
 * The site never computes its own numbers and never hardcodes them here —
 * every figure below is read from the JSON at build time. Derived figures
 * (sums, shares, staleness) are computed from that JSON, never typed. */

export interface BronzeSource {
  source: string;
  family: string;
  ingest_date: string;
  rows_landed: number;
  rows_reported: number | null;
  count_match: boolean | null;
  status: string;
}

export interface PermitsIssuedRow {
  municipality: string;
  year: number;
  permits_issued: number;
}

export interface PermitsStatusRow {
  municipality: string;
  status: string;
  permits: number;
}

export interface ApplicationsStatusRow {
  municipality: string;
  status: string;
  applications: number;
}

export interface PermitMedianDays {
  permits_with_both_dates: number;
  median_days: number;
}

export interface ApplicationMedianDays {
  applications_with_both_dates: number;
  median_days: number;
}

export interface ConstructionValue {
  total_cad: number | null;
  permit_rows: number;
  null_value_rows: number;
}

export interface NetUnits {
  net_units: number | null;
  permit_rows: number;
  null_unit_rows: number;
}

interface Reconciliation {
  meta: { generated_at_utc: string; git_sha: string | null; source: string };
  fact_totals: { fct_permits: number; fct_applications: number };
  bronze: { ingest_date: string; sources: BronzeSource[] };
  permits_by_municipality: Record<string, number>;
  permits_issued_by_municipality_year: PermitsIssuedRow[];
  permits_by_municipality_status: PermitsStatusRow[];
  applications_by_municipality_status: ApplicationsStatusRow[];
  permit_applied_to_issued_median_days: Record<string, PermitMedianDays>;
  application_submitted_to_decision_median_days: Record<
    string,
    ApplicationMedianDays
  >;
  construction_value_cad_by_municipality: Record<string, ConstructionValue>;
  net_units_by_municipality: Record<string, NetUnits>;
  integrity: {
    orphan_permit_fks: number;
    orphan_application_fks: number;
    permits_null_geography: number;
    applications_null_geography: number;
    permits_unknown_use: number;
    applications_unknown_use: number;
  };
  unit_basis: string;
  pending_measures: Record<string, string>;
}

const data = recon as unknown as Reconciliation;

export const meta = data.meta;
export const factTotals = data.fact_totals;
export const bronze = data.bronze;
export const permitsByMunicipality = data.permits_by_municipality;
export const permitsIssuedByMunicipalityYear =
  data.permits_issued_by_municipality_year;
export const permitsByMunicipalityStatus = data.permits_by_municipality_status;
export const applicationsByMunicipalityStatus =
  data.applications_by_municipality_status;
export const permitAppliedToIssuedMedianDays =
  data.permit_applied_to_issued_median_days;
export const applicationSubmittedToDecisionMedianDays =
  data.application_submitted_to_decision_median_days;
export const constructionValueCadByMunicipality =
  data.construction_value_cad_by_municipality;
export const netUnitsByMunicipality = data.net_units_by_municipality;
export const integrity = data.integrity;
export const unitBasis = data.unit_basis;
export const pendingMeasures = data.pending_measures;

/* Municipality codes are internal keys; a visitor never sees one. */
export const MUNICIPALITY_NAMES: Record<string, string> = {
  TOR: "Toronto",
  MISS: "Mississauga",
  BRAM: "Brampton",
};

export function municipalityName(code: string): string {
  const name = MUNICIPALITY_NAMES[code];
  if (name === undefined) {
    // Fail the build rather than leak a raw code into the page.
    throw new Error(`No display name for municipality code "${code}"`);
  }
  return name;
}

/** Municipality codes ordered by permit records, largest first (derived). */
export function municipalityCodes(): string[] {
  return Object.keys(permitsByMunicipality).sort(
    (a, b) => permitsByMunicipality[b] - permitsByMunicipality[a],
  );
}

export function formatInt(n: number | null): string {
  if (n === null || n === undefined) return "not yet measured";
  return n.toLocaleString("en-CA");
}

export function feedsOk(): { ok: number; total: number } {
  const ok = bronze.sources.filter((s) => s.status === "ok").length;
  return { ok, total: bronze.sources.length };
}

export const REPO_URL = "https://github.com/Halomaster0/GTA-Housing-pipeline";

/* ---------- Formatting ---------- */

/** num/den as a percentage string; an explicit empty state if den is 0. */
export function formatPct(num: number, den: number, digits = 1): string {
  if (!den) return "not yet measured";
  const pct = (num / den) * 100;
  const text = pct.toFixed(digits);
  // A non-zero share must never round down to a flat "0.0%".
  if (num > 0 && Number(text) === 0)
    return `<${(10 ** -digits).toFixed(digits)}%`;
  return `${text}%`;
}

export function formatDays(n: number): string {
  return Number.isInteger(n) ? n.toLocaleString("en-CA") : n.toFixed(1);
}

/** Whole Canadian dollars; null stays an explicit empty state. */
export function formatCad(n: number | null): string {
  if (n === null || n === undefined) return "not yet measured";
  return Math.round(n).toLocaleString("en-CA");
}

/* ---------- Provenance and freshness ---------- */

export const asOfDate = meta.generated_at_utc.slice(0, 10);
export const asOfYear = Number(asOfDate.slice(0, 4));

/** The chart-frame provenance line (design-plan §5): file, git sha, as-of date. */
export function provenanceLine(): string {
  const sha = meta.git_sha ?? "not recorded";
  return `Source: docs/measure-reconciliation.json, git_sha ${sha}, as of ${asOfDate}`;
}

/* The declared refresh cadence is weekly (docs/handovers/HANDOVER-7.md; the
 * refresh itself is manual until automated). The freshness rule in the build
 * plan is "stale beyond 2x the declared cadence". Both are rules, not data. */
export const REFRESH_CADENCE_DAYS = 7;
export const STALE_AFTER_DAYS = 2 * REFRESH_CADENCE_DAYS;

/** Whole UTC calendar days from the ISO timestamp to `now`. */
export function daysSince(iso: string, now: Date): number {
  const utcDay = (d: Date) =>
    Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate());
  return Math.round((utcDay(now) - utcDay(new Date(iso))) / 86_400_000);
}

/* ---------- Permits: issued versus all records ---------- */

/** Permits issued per municipality: the by-year series summed. That series is
 * built with an INNER JOIN on date_issued_sk to dim_date
 * (scripts/reconcile_measures.py), so it counts only records that carry an
 * issue date inside the date dimension. */
export function permitsIssuedByMunicipality(): Record<string, number> {
  const out: Record<string, number> = {};
  for (const r of permitsIssuedByMunicipalityYear) {
    out[r.municipality] = (out[r.municipality] ?? 0) + r.permits_issued;
  }
  return out;
}

export function permitsIssuedTotal(): number {
  return Object.values(permitsIssuedByMunicipality()).reduce(
    (a, b) => a + b,
    0,
  );
}

/** Sum of permit records at the given statuses, optionally for one municipality. */
export function permitsAtStatus(statuses: string[], code?: string): number {
  return permitsByMunicipalityStatus
    .filter(
      (r) =>
        statuses.includes(r.status) &&
        (code === undefined || r.municipality === code),
    )
    .reduce((a, r) => a + r.permits, 0);
}

function hasStatusRows(statuses: string[], code: string): boolean {
  return permitsByMunicipalityStatus.some(
    (r) => statuses.includes(r.status) && r.municipality === code,
  );
}

export interface IssuedGap {
  code: string;
  records: number;
  issued: number;
  excluded: number;
  /** Permit records at APPLIED or UNDER_REVIEW, shown beside the gap. Null when
   * the feed has no rows at either status (an absence, not a zero). */
  pending: number | null;
}

export function permitIssuedGap(): IssuedGap[] {
  const issued = permitsIssuedByMunicipality();
  return municipalityCodes().map((code) => {
    const records = permitsByMunicipality[code];
    const n = issued[code] ?? 0;
    return {
      code,
      records,
      issued: n,
      excluded: records - n,
      pending: hasStatusRows(["APPLIED", "UNDER_REVIEW"], code)
        ? permitsAtStatus(["APPLIED", "UNDER_REVIEW"], code)
        : null,
    };
  });
}

/* ---------- Status mixes (derived by summing the committed breakdowns) ---------- */

export interface StatusTotal {
  status: string;
  count: number;
}

function totalsByStatus(
  rows: Array<{ status: string; n: number }>,
): StatusTotal[] {
  const t = new Map<string, number>();
  for (const r of rows) t.set(r.status, (t.get(r.status) ?? 0) + r.n);
  return [...t.entries()]
    .map(([status, count]) => ({ status, count }))
    .sort((a, b) => b.count - a.count);
}

export function permitStatusTotals(): StatusTotal[] {
  return totalsByStatus(
    permitsByMunicipalityStatus.map((r) => ({
      status: r.status,
      n: r.permits,
    })),
  );
}

export function applicationStatusTotals(): StatusTotal[] {
  return totalsByStatus(
    applicationsByMunicipalityStatus.map((r) => ({
      status: r.status,
      n: r.applications,
    })),
  );
}

export function applicationsByMunicipality(): Record<string, number> {
  const out: Record<string, number> = {};
  for (const r of applicationsByMunicipalityStatus) {
    out[r.municipality] = (out[r.municipality] ?? 0) + r.applications;
  }
  return out;
}

/* ---------- Year series ---------- */

export function yearSpan(): { first: number; last: number } {
  const years = permitsIssuedByMunicipalityYear.map((r) => r.year);
  return { first: Math.min(...years), last: Math.max(...years) };
}

export function firstYearByMunicipality(): Record<string, number> {
  const out: Record<string, number> = {};
  for (const r of permitsIssuedByMunicipalityYear) {
    if (out[r.municipality] === undefined || r.year < out[r.municipality]) {
      out[r.municipality] = r.year;
    }
  }
  return out;
}

/* ---------- Build-time reconciliation guard ---------- */

/** Throws (failing the build) if any figure the dashboard derives does not
 * tie back to the fact totals. A page that disagrees with its own source file
 * must not ship. */
export function reconcileOrThrow(): void {
  const problems: string[] = [];
  const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);

  if (sum(Object.values(permitsByMunicipality)) !== factTotals.fct_permits) {
    problems.push("permits_by_municipality does not sum to fct_permits");
  }
  if (
    sum(permitsByMunicipalityStatus.map((r) => r.permits)) !==
    factTotals.fct_permits
  ) {
    problems.push("permits_by_municipality_status does not sum to fct_permits");
  }
  if (
    sum(applicationsByMunicipalityStatus.map((r) => r.applications)) !==
    factTotals.fct_applications
  ) {
    problems.push(
      "applications_by_municipality_status does not sum to fct_applications",
    );
  }
  for (const [code, records] of Object.entries(permitsByMunicipality)) {
    if (
      permitsAtStatus(
        permitStatusTotals().map((s) => s.status),
        code,
      ) !== records
    ) {
      problems.push(`permit status rows for ${code} do not sum to its records`);
    }
    if ((permitsIssuedByMunicipality()[code] ?? 0) > records) {
      problems.push(`permits issued exceeds permit records for ${code}`);
    }
    if (netUnitsByMunicipality[code]?.permit_rows !== records) {
      problems.push(`net_units permit_rows differs from records for ${code}`);
    }
    if (constructionValueCadByMunicipality[code]?.permit_rows !== records) {
      problems.push(`construction value permit_rows differs for ${code}`);
    }
    const med = permitAppliedToIssuedMedianDays[code];
    if (med && med.permits_with_both_dates > records) {
      problems.push(`median-days n exceeds permit records for ${code}`);
    }
  }
  const appsBy = applicationsByMunicipality();
  for (const [code, m] of Object.entries(
    applicationSubmittedToDecisionMedianDays,
  )) {
    if (m.applications_with_both_dates > (appsBy[code] ?? 0)) {
      problems.push(`decision-days n exceeds applications for ${code}`);
    }
  }
  if (problems.length > 0) {
    throw new Error(`Reconciliation guard failed:\n- ${problems.join("\n- ")}`);
  }
}
