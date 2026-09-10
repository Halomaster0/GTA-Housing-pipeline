import recon from "../../docs/measure-reconciliation.json";

/* Typed accessors over the committed reconciliation file (ADR-0008/0009).
 * The site never computes its own numbers and never hardcodes them here —
 * every figure below is read from the JSON at build time. */

export interface BronzeSource {
  source: string;
  family: string;
  ingest_date: string;
  rows_landed: number;
  rows_reported: number | null;
  count_match: boolean | null;
  status: string;
}

interface Reconciliation {
  meta: { generated_at_utc: string; git_sha: string | null; source: string };
  fact_totals: { fct_permits: number; fct_applications: number };
  bronze: { ingest_date: string; sources: BronzeSource[] };
  permits_by_municipality: Record<string, number>;
  net_units_by_municipality: Record<
    string,
    { net_units: number | null; permit_rows: number; null_unit_rows: number }
  >;
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
export const netUnitsByMunicipality = data.net_units_by_municipality;
export const integrity = data.integrity;
export const unitBasis = data.unit_basis;
export const pendingMeasures = data.pending_measures;

export function formatInt(n: number | null): string {
  if (n === null || n === undefined) return "not yet measured";
  return n.toLocaleString("en-CA");
}

export function feedsOk(): { ok: number; total: number } {
  const ok = bronze.sources.filter((s) => s.status === "ok").length;
  return { ok, total: bronze.sources.length };
}

export const REPO_URL = "https://github.com/Halomaster0/GTA-Housing-pipeline";
