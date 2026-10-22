import type { Metadata } from "next";
import { ChartFrame } from "../../components/ChartFrame";
import { HBarChart, type HBarItem } from "../../components/HBarChart";
import { ScrollTable } from "../../components/ScrollTable";
import { StackedYearChart, YearTable } from "../../components/StackedYearChart";
import { StatusMatrix } from "../../components/StatusMatrix";
import {
  REPO_URL,
  STALE_AFTER_DAYS,
  REFRESH_CADENCE_DAYS,
  applicationStatusTotals,
  applicationSubmittedToDecisionMedianDays,
  applicationsByMunicipality,
  applicationsByMunicipalityStatus,
  asOfDate,
  constructionValueCadByMunicipality,
  daysSince,
  factTotals,
  firstYearByMunicipality,
  formatCad,
  formatDays,
  formatInt,
  formatPct,
  meta,
  municipalityCodes,
  municipalityName,
  netUnitsByMunicipality,
  pendingMeasures,
  permitAppliedToIssuedMedianDays,
  permitIssuedGap,
  permitStatusTotals,
  permitsAtStatus,
  permitsByMunicipality,
  permitsByMunicipalityStatus,
  permitsIssuedByMunicipalityYear,
  permitsIssuedTotal,
  provenanceLine,
  reconcileOrThrow,
  unitBasis,
  yearSpan,
} from "../../lib/measures";

export const metadata: Metadata = {
  title: "Dashboard",
  description:
    "Reconciled gold-layer figures: permits issued versus permit records, application status, processing times, and unit counts with their comparability caveat. Not an embedded Power BI report.",
};

const DOCS = `${REPO_URL}/blob/main/docs`;

/* Source expression behind each municipality's unit_count_net_new
 * (models/gold/05_fct_permits.sql; docs/reviews/powerbi-build-review-2026-10-22.md D1). */
const UNIT_EXPRESSION: Record<string, string> = {
  TOR: "dwelling_units_created minus dwelling_units_lost (net)",
  MISS: "res_units as supplied (gross)",
  BRAM: "dwellings as supplied (gross)",
};

const PENDING_TITLES: Record<string, string> = {
  units_per_capita: "Units per capita",
  application_to_permit_days: "Application to permit timing",
  statcan_control_totals: "StatCan control totals",
  brampton_construction_value: "Brampton construction value",
};

/* Pending measures that sit beside the figures they would extend. Any other
 * key in the file is listed in the closing section so none can vanish silently. */
const PLACED_IN_CONTEXT = [
  "units_per_capita",
  "application_to_permit_days",
  "brampton_construction_value",
];

function Pending({ measureKey }: { measureKey: string }) {
  const title = PENDING_TITLES[measureKey] ?? measureKey.replace(/_/g, " ");
  const reason = pendingMeasures[measureKey];
  return (
    <div className="empty compact">
      <h3>{title}</h3>
      <p>
        <strong>Not yet measured.</strong>{" "}
        {reason ??
          "No reason is recorded for this measure in docs/measure-reconciliation.json."}
      </p>
    </div>
  );
}

function statusSentence(items: Array<{ status: string; count: number }>) {
  return items.map((s) => `${s.status} ${formatInt(s.count)}`).join(", ");
}

export default function Dashboard() {
  // A page that disagrees with its own source file must not ship.
  reconcileOrThrow();

  const now = new Date();
  const buildDate = now.toISOString().slice(0, 10);
  const staleDays = daysSince(meta.generated_at_utc, now);
  const isStale = staleDays > STALE_AFTER_DAYS;

  const codes = municipalityCodes();
  const span = yearSpan();
  const firstYear = firstYearByMunicipality();
  const issuedTotal = permitsIssuedTotal();
  const recordsTotal = factTotals.fct_permits;
  const gap = permitIssuedGap();
  const gapTotal = recordsTotal - issuedTotal;
  const cancelledTotal = permitsAtStatus(["CANCELLED"]);
  const pendingStatusTotal = permitsAtStatus(["APPLIED", "UNDER_REVIEW"]);
  const largeGaps = gap.filter((g) => g.excluded > (g.pending ?? 0));
  const noGaps = gap.filter((g) => g.excluded === 0);

  const permitStatuses = permitStatusTotals();
  const appStatuses = applicationStatusTotals();
  const appTotal = appStatuses.reduce((a, s) => a + s.count, 0);
  const appsBy = applicationsByMunicipality();

  const statusItems = (
    totals: Array<{ status: string; count: number }>,
    total: number,
  ): HBarItem[] =>
    totals.map((s) => ({
      label: s.status,
      value: s.count,
      valueText: `${formatInt(s.count)} (${formatPct(s.count, total)})`,
    }));

  const medianItems: HBarItem[] = Object.entries(
    permitAppliedToIssuedMedianDays,
  )
    .sort((a, b) => a[1].median_days - b[1].median_days)
    .map(([code, v]) => ({
      label: municipalityName(code),
      value: v.median_days,
      valueText: `${formatDays(v.median_days)} days`,
      detail: `n = ${formatInt(v.permits_with_both_dates)} permits, ${formatPct(
        v.permits_with_both_dates,
        permitsByMunicipality[code],
      )} of permit records`,
    }));

  const decisionEntries = Object.entries(
    applicationSubmittedToDecisionMedianDays,
  );
  const noDecisionCodes = codes.filter(
    (c) => applicationSubmittedToDecisionMedianDays[c] === undefined,
  );

  const otherPending = Object.keys(pendingMeasures).filter(
    (k) => !PLACED_IN_CONTEXT.includes(k),
  );

  const lateStarts = codes.filter((c) => firstYear[c] > span.first);

  return (
    <>
      <h1>Dashboard</h1>
      <p>
        This page is not an embedded Power BI report. The Power BI semantic
        model and DAX measure library are committed in the repository (
        <a href={`${DOCS}/fabric-dax.md`} rel="noopener">
          docs/fabric-dax.md
        </a>
        ,{" "}
        <a href={`${DOCS}/data-dictionary.md`} rel="noopener">
          docs/data-dictionary.md
        </a>
        ). This page renders figures computed from the same gold tables, read
        directly from <code>docs/measure-reconciliation.json</code>, so it works
        without a Fabric tenant.
      </p>

      <section aria-labelledby="freshness-heading">
        <h2 id="freshness-heading">Freshness</h2>
        <div className="status">
          <span
            className={`dot ${isStale ? "stale" : "live"}`}
            aria-hidden="true"
          />
          <div>
            <div className="word">{isStale ? "Stale" : "Live"}</div>
            <div className="sub">
              {staleDays} {staleDays === 1 ? "day" : "days"} since the data was
              generated
            </div>
            <div className="sub">
              {isStale
                ? `Exceeds 2x the weekly refresh cadence (${STALE_AFTER_DAYS} days)`
                : `Within 2x the weekly refresh cadence (${STALE_AFTER_DAYS} days)`}
              . Measured when this site was built, {buildDate}. Refresh is
              manual until automated; the cadence is {REFRESH_CADENCE_DAYS}{" "}
              days.
            </div>
          </div>
        </div>
        <p className="provenance">
          Data as of {asOfDate}, git_sha {meta.git_sha ?? "not recorded"}.
        </p>
      </section>

      <div className="metric-row">
        <div className="metric">
          <div className="value gold">{formatInt(issuedTotal)}</div>
          <div className="label">
            Permits issued, {span.first} to {span.last}: permit records with an
            issue date, summed from the by-year series below
          </div>
        </div>
        <div className="metric">
          <div className="value">{formatInt(recordsTotal)}</div>
          <div className="label">
            Permit records (all statuses): every permit row in the gold table
          </div>
        </div>
        <div className="metric">
          <div className="value">{formatInt(factTotals.fct_applications)}</div>
          <div className="label">
            Applications (all statuses): every development application row
          </div>
        </div>
      </div>

      <h2>Permits issued and permit records</h2>
      <p>
        These are two different counts. Permit records is every permit row in
        the gold table, whatever its status. Permits issued keeps only records
        that carry an issue date inside the date dimension.
      </p>
      <ScrollTable label="Permits issued against permit records by municipality, scrollable">
        <table className="data">
          <caption>
            {gap.length} municipalities, with a total row. Permit counts are
            comparable across municipalities; unit counts are not (see net new
            units below).
          </caption>
          <thead>
            <tr>
              <th scope="col">Municipality</th>
              <th scope="col" className="num">
                Permit records (all statuses)
              </th>
              <th scope="col" className="num">
                Permits issued
              </th>
              <th scope="col" className="num">
                Not in the issued count
              </th>
              <th scope="col" className="num">
                Share not in the issued count
              </th>
              <th scope="col" className="num">
                Records at APPLIED or UNDER_REVIEW
              </th>
            </tr>
          </thead>
          <tbody>
            {gap.map((g) => (
              <tr key={g.code}>
                <th scope="row">{municipalityName(g.code)}</th>
                <td className="num">{formatInt(g.records)}</td>
                <td className="num">{formatInt(g.issued)}</td>
                <td className="num">{formatInt(g.excluded)}</td>
                <td className="num">{formatPct(g.excluded, g.records)}</td>
                {g.pending === null ? (
                  <td className="num na">none recorded</td>
                ) : (
                  <td className="num">{formatInt(g.pending)}</td>
                )}
              </tr>
            ))}
            <tr>
              <th scope="row">All three</th>
              <td className="num">{formatInt(recordsTotal)}</td>
              <td className="num">{formatInt(issuedTotal)}</td>
              <td className="num">{formatInt(gapTotal)}</td>
              <td className="num">{formatPct(gapTotal, recordsTotal)}</td>
              <td className="num">{formatInt(pendingStatusTotal)}</td>
            </tr>
          </tbody>
        </table>
      </ScrollTable>
      <p className="provenance">{provenanceLine()}</p>
      <p>
        The {formatInt(recordsTotal)} figure counts every permit record
        regardless of status: {formatInt(pendingStatusTotal)} are at{" "}
        <code>APPLIED</code> or <code>UNDER_REVIEW</code>, and a further{" "}
        {formatInt(cancelledTotal)} are <code>CANCELLED</code>.
      </p>
      <p>
        The {formatInt(gapTotal)} records outside the issued count have two
        causes this file cannot separate. A record drops out if it has no issue
        date (records still at <code>APPLIED</code> or <code>UNDER_REVIEW</code>{" "}
        would not yet have one), or if its issue date falls before 2010, which
        the date dimension (2010-01-01 to 2028-12-31, per
        docs/data-dictionary.md) does not cover.
      </p>
      {largeGaps.length > 0 ? (
        <>
          <ul>
            {largeGaps.map((g) => (
              <li key={g.code}>
                {municipalityName(g.code)}: {formatInt(g.excluded)} records are
                not in the issued count,{" "}
                {g.pending === null
                  ? "and none are recorded at "
                  : `against ${formatInt(g.pending)} at `}
                <code>APPLIED</code> or <code>UNDER_REVIEW</code>.
              </li>
            ))}
          </ul>
          <p>
            For {largeGaps.map((g) => municipalityName(g.code)).join(" and ")},
            most of this gap is likely permits issued before 2010, which the
            date dimension does not cover. The file does not record the split,
            so none is asserted.
          </p>
        </>
      ) : null}
      {noGaps.map((g) => (
        <p key={g.code}>
          {municipalityName(g.code)} has no gap: all {formatInt(g.records)} of
          its permit records have an issue date inside the window, consistent
          with its feed starting in {firstYear[g.code]}.
        </p>
      ))}

      <ChartFrame
        id="permit-status"
        title="Permit records by status"
        caption={
          <>
            Current status of every permit record, all municipalities together.
            The status mix is part of why the record count is larger than the
            issued count. A status is a permit&apos;s current state, so the{" "}
            {formatInt(permitsAtStatus(["ISSUED"]))} records at{" "}
            <code>ISSUED</code> are not the same measure as permits issued (
            {formatInt(issuedTotal)}); this file does not break issue date down
            by status.
          </>
        }
        tableSummary="Permit records by status and municipality, as a table"
        tableOpen
        table={
          <StatusMatrix
            rows={permitsByMunicipalityStatus.map((r) => ({
              municipality: r.municipality,
              status: r.status,
              count: r.permits,
            }))}
            codes={codes}
            noun="municipalities"
            scrollLabel="Permit records by status and municipality, scrollable"
            caption={`${permitStatuses.length} statuses by ${codes.length} municipalities, ${formatInt(recordsTotal)} permit records in all. None recorded means the feed has no records in that status for that municipality.`}
          />
        }
      >
        <HBarChart
          items={statusItems(permitStatuses, recordsTotal)}
          ariaLabel={`Horizontal bar chart of ${formatInt(recordsTotal)} permit records by status, largest first: ${statusSentence(permitStatuses)}. The same figures by municipality are in the table below.`}
        />
      </ChartFrame>

      <ChartFrame
        id="permits-by-year"
        title="Permits issued by year"
        caption={
          <>
            Permits issued per calendar year of issue date, stacked by
            municipality, {span.first} to {span.last}. {span.last} is partial:
            the data runs to {asOfDate}. Series start years:{" "}
            {codes
              .map((c) => `${municipalityName(c)} ${firstYear[c]}`)
              .join(", ")}
            .
            {lateStarts.length > 0
              ? ` The stack changes composition at ${Math.max(
                  ...lateStarts.map((c) => firstYear[c]),
                )}, so totals before and after that year are not like for like.`
              : ""}
          </>
        }
        tableSummary="Permits issued by year and municipality, as a table"
        table={
          <YearTable rows={permitsIssuedByMunicipalityYear} order={codes} />
        }
      >
        <StackedYearChart
          rows={permitsIssuedByMunicipalityYear}
          order={codes}
        />
      </ChartFrame>

      <h2>Applications by status</h2>
      <p>
        {formatInt(appTotal)} development applications across{" "}
        {Object.keys(appsBy).length} municipalities. Every status carries its
        value; the bars are sorted largest first.
      </p>
      <ChartFrame
        id="application-status"
        title="Application status mix"
        caption={
          <>
            Current status of every application in the gold table. The bars sum
            to {formatInt(appTotal)}, which matches the gold application count.
          </>
        }
        tableSummary="Applications by status and municipality, as a table"
        table={
          <StatusMatrix
            rows={applicationsByMunicipalityStatus.map((r) => ({
              municipality: r.municipality,
              status: r.status,
              count: r.applications,
            }))}
            codes={codes}
            noun="municipalities"
            scrollLabel="Applications by status and municipality, scrollable"
            caption={`${appStatuses.length} statuses by ${codes.length} municipalities, ${formatInt(appTotal)} applications in all. None recorded means the feed has no applications in that status for that municipality.`}
          />
        }
      >
        <HBarChart
          items={statusItems(appStatuses, appTotal)}
          ariaLabel={`Sorted horizontal bar chart of ${formatInt(appTotal)} applications by status: ${statusSentence(appStatuses)}. The same figures by municipality are in the table below.`}
        />
      </ChartFrame>

      <h2>How long permits and decisions take</h2>
      <p>
        Median days from the applied date to the issued date, over permits that
        have both dates. This is a comparison on a basis that is comparable
        across municipalities.
      </p>
      <ChartFrame
        id="applied-to-issued"
        title="Median days from applied to issued"
        caption={
          <>
            Median calendar days between the applied date and the issued date.
            The share beside each is the permits with both dates as a percentage
            of all permit records for that municipality. Records whose dates
            fall outside the date dimension (2010 to 2028) are not counted.
          </>
        }
        tableSummary="Median days from applied to issued, as a table"
        tableOpen
        table={
          <ScrollTable label="Median days from applied to issued by municipality, scrollable">
            <table className="data">
              <caption>
                {medianItems.length} municipalities, fastest first.
              </caption>
              <thead>
                <tr>
                  <th scope="col">Municipality</th>
                  <th scope="col" className="num">
                    Median days
                  </th>
                  <th scope="col" className="num">
                    Permits with both dates
                  </th>
                  <th scope="col" className="num">
                    Share of permit records
                  </th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(permitAppliedToIssuedMedianDays)
                  .sort((a, b) => a[1].median_days - b[1].median_days)
                  .map(([code, v]) => (
                    <tr key={code}>
                      <th scope="row">{municipalityName(code)}</th>
                      <td className="num">{formatDays(v.median_days)}</td>
                      <td className="num">
                        {formatInt(v.permits_with_both_dates)}
                      </td>
                      <td className="num">
                        {formatPct(
                          v.permits_with_both_dates,
                          permitsByMunicipality[code],
                        )}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </ScrollTable>
        }
      >
        <HBarChart
          items={medianItems}
          ariaLabel={`Horizontal bar chart of median days from applied to issued, fastest first: ${medianItems
            .map((i) => `${i.label} ${i.valueText}, ${i.detail}`)
            .join("; ")}. The same figures are in the table below.`}
        />
      </ChartFrame>

      <h3>Submitted to decision, applications</h3>
      {decisionEntries.map(([code, v]) => (
        <div className="metric" key={code}>
          <div className="value">{formatDays(v.median_days)} days</div>
          <div className="label">
            {municipalityName(code)}: median days from submitted to decision,
            over {formatInt(v.applications_with_both_dates)} applications (
            {formatPct(v.applications_with_both_dates, appsBy[code] ?? 0)} of
            its applications)
          </div>
        </div>
      ))}
      {noDecisionCodes.map((code) => (
        <div className="empty compact" key={code}>
          <h3>{municipalityName(code)} submitted to decision</h3>
          <p>
            <strong>Not yet measured.</strong> No decision dates in the source
            feed (docs/report-plan.md, page 3).
          </p>
        </div>
      ))}
      <Pending measureKey="application_to_permit_days" />

      <h2>Net new units, per municipality</h2>
      <div className="notice" role="note">
        <h3>Unit counts are not comparable across municipalities</h3>
        <p>
          The basis recorded in the reconciliation file is{" "}
          <code>{unitBasis}</code>.
        </p>
        <p>
          Toronto&apos;s figure is dwelling units created minus dwelling units
          lost, a net value. Mississauga&apos;s and Brampton&apos;s are the unit
          counts their feeds supply, with nothing subtracted. Adding them would
          add a net quantity to two gross ones, so this page shows no combined
          total and no cross-municipality ranking. See{" "}
          <a href={`${DOCS}/decisions/0003-unit-count-basis.md`} rel="noopener">
            ADR-0003
          </a>
          .
        </p>
      </div>
      <ScrollTable label="Net new units by municipality with unit coverage, scrollable">
        <table className="data">
          <caption>
            {codes.length} municipalities, read one row at a time. There is no
            total row. Units are summed over records that carry a count; records
            with no count are left out, not treated as zero.
          </caption>
          <thead>
            <tr>
              <th scope="col">Municipality</th>
              <th scope="col">Unit expression in the gold table</th>
              <th scope="col" className="num">
                Net new units, as reported
              </th>
              <th scope="col" className="num">
                Permit records
              </th>
              <th scope="col" className="num">
                Records with no unit count
              </th>
              <th scope="col" className="num">
                Share with no unit count
              </th>
            </tr>
          </thead>
          <tbody>
            {codes.map((code) => {
              const u = netUnitsByMunicipality[code];
              return (
                <tr key={code}>
                  <th scope="row">{municipalityName(code)}</th>
                  <td>{UNIT_EXPRESSION[code] ?? "not documented"}</td>
                  <td className="num">{formatInt(u?.net_units ?? null)}</td>
                  <td className="num">{formatInt(u?.permit_rows ?? null)}</td>
                  <td className="num">
                    {formatInt(u?.null_unit_rows ?? null)}
                  </td>
                  <td className="num">
                    {u
                      ? formatPct(u.null_unit_rows, u.permit_rows)
                      : "not yet measured"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </ScrollTable>
      <p className="provenance">
        {`${provenanceLine()}. Unit expressions: models/gold/05_fct_permits.sql.`}
      </p>
      <Pending measureKey="units_per_capita" />

      <h2>Construction value</h2>
      <p>
        Declared construction value in Canadian dollars, shown per municipality
        and not totalled: the feeds differ in how much of this field they fill.
      </p>
      <ScrollTable label="Construction value by municipality, scrollable">
        <table className="data">
          <caption>
            {codes.length} municipalities. Value is summed over records that
            carry one; records with no value are left out, not treated as zero.
          </caption>
          <thead>
            <tr>
              <th scope="col">Municipality</th>
              <th scope="col" className="num">
                Total declared value (CAD)
              </th>
              <th scope="col" className="num">
                Permit records
              </th>
              <th scope="col" className="num">
                Records with no value
              </th>
              <th scope="col" className="num">
                Share with no value
              </th>
            </tr>
          </thead>
          <tbody>
            {codes.map((code) => {
              const v = constructionValueCadByMunicipality[code];
              return (
                <tr key={code}>
                  <th scope="row">{municipalityName(code)}</th>
                  <td className="num">{formatCad(v?.total_cad ?? null)}</td>
                  <td className="num">{formatInt(v?.permit_rows ?? null)}</td>
                  <td className="num">
                    {formatInt(v?.null_value_rows ?? null)}
                  </td>
                  <td className="num">
                    {v
                      ? formatPct(v.null_value_rows, v.permit_rows)
                      : "not yet measured"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </ScrollTable>
      <p className="provenance">{provenanceLine()}</p>
      <Pending measureKey="brampton_construction_value" />

      {otherPending.length > 0 ? (
        <>
          <h2>Other measures not yet available</h2>
          {otherPending.map((k) => (
            <Pending measureKey={k} key={k} />
          ))}
        </>
      ) : null}

      <h2>Reproducing these figures</h2>
      <p>
        Every figure above is read from{" "}
        <a
          href={`${REPO_URL}/blob/main/docs/measure-reconciliation.json`}
          rel="noopener"
        >
          docs/measure-reconciliation.json
        </a>
        , written by{" "}
        <a
          href={`${REPO_URL}/blob/main/scripts/reconcile_measures.py`}
          rel="noopener"
        >
          scripts/reconcile_measures.py
        </a>{" "}
        (run with <code>make reconcile</code>). Totals shown here are computed
        from that file at build time and checked against the gold row counts;
        the build fails if they disagree.
      </p>
    </>
  );
}
