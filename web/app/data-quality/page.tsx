import type { Metadata } from "next";
import {
  factTotals,
  formatInt,
  integrity,
  pendingMeasures,
  unitBasis,
} from "../../lib/measures";

export const metadata: Metadata = {
  title: "Data quality and freshness",
  description:
    "Last refresh, row counts, integrity checks, and known gaps — the page a sceptic opens first.",
};

export default function DataQuality() {
  const pending = Object.entries(pendingMeasures);
  return (
    <>
      <h1>Data quality and freshness</h1>
      <p>
        Every number below is read at build time from{" "}
        <code>docs/measure-reconciliation.json</code>. A dashboard figure that
        disagrees with this page is wrong until proven otherwise.
      </p>

      <div className="metric">
        <div className="value gold">{formatInt(factTotals.fct_permits)}</div>
        <div className="label">Gold fact rows: permits</div>
      </div>
      <div className="metric">
        <div className="value">{formatInt(factTotals.fct_applications)}</div>
        <div className="label">Gold fact rows: applications</div>
      </div>

      <h2>Integrity checks</h2>
      {/* See landing page note: design-plan §7 scroll-region pattern;
          disable/enable pair because the rule reports at the prop line. */}
      {/* eslint-disable jsx-a11y/no-noninteractive-tabindex -- design-plan §7 */}
      <div
        className="table-scroll"
        tabIndex={0}
        role="region"
        aria-label="Integrity check results, scrollable"
      >
        <table className="data">
          <caption>
            6 integrity checks. Orphan foreign keys must be zero; the rest are
            measured and explained, not hidden.
          </caption>
          <thead>
            <tr>
              <th scope="col">Check</th>
              <th scope="col" className="num">
                Count
              </th>
              <th scope="col">Reading</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Orphan permit foreign keys</td>
              <td className="num">{formatInt(integrity.orphan_permit_fks)}</td>
              <td>Must be zero</td>
            </tr>
            <tr>
              <td>Orphan application foreign keys</td>
              <td className="num">
                {formatInt(integrity.orphan_application_fks)}
              </td>
              <td>Must be zero</td>
            </tr>
            <tr>
              <td>Permits with null geography</td>
              <td className="num">
                {formatInt(integrity.permits_null_geography)}
              </td>
              <td>Toronto grid references are not wards; Brampton permits carry no ward</td>
            </tr>
            <tr>
              <td>Applications with null geography</td>
              <td className="num">
                {formatInt(integrity.applications_null_geography)}
              </td>
              <td>Unmatched ward codes, measured residual</td>
            </tr>
            <tr>
              <td>Permits with unknown use type</td>
              <td className="num">{formatInt(integrity.permits_unknown_use)}</td>
              <td>Crosswalk grows deliberately (conformance matrix)</td>
            </tr>
            <tr>
              <td>Applications with unknown use type</td>
              <td className="num">
                {formatInt(integrity.applications_unknown_use)}
              </td>
              <td>Toronto process codes carry no use signal</td>
            </tr>
          </tbody>
        </table>
        {/* eslint-enable jsx-a11y/no-noninteractive-tabindex */}
      </div>

      <h2>Unit basis</h2>
      <p>
        All gold unit measures carry <code>unit_count_basis</code> of{" "}
        <code>{unitBasis}</code>: unit counts are not comparable across
        municipalities without the per-source appendices (ADR-0003).
      </p>

      <h2>Pending measures</h2>
      <p>
        Defined but uncomputable. Each appears here as an explicit statement,
        never a zero:
      </p>
      <ul>
        {pending.map(([name, reason]) => (
          <li key={name}>
            <strong>{name}</strong> — {reason}
          </li>
        ))}
      </ul>
    </>
  );
}
