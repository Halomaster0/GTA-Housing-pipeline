import type { Metadata } from "next";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import {
  bronze,
  factTotals,
  feedsOk,
  formatInt,
  permitsByMunicipality,
} from "../lib/measures";

export const metadata: Metadata = {
  description:
    "Live pipeline status and gold-layer totals for the GTA Housing Pipeline.",
};

function loadMapSvg(): string {
  return readFileSync(join(process.cwd(), "public", "gta-map.svg"), "utf-8");
}

export default function Home() {
  const feeds = feedsOk();
  const allOk = feeds.ok === feeds.total;
  const mapSvg = loadMapSvg();
  const muniNames: Record<string, string> = {
    TOR: "Toronto",
    MISS: "Mississauga",
    BRAM: "Brampton",
  };

  return (
    <>
      <div className="split">
        <div>
          <h1>
            This pipeline ingests GTA municipal open-data feeds into one
            queryable model, and answers plain-English questions against it —
            grounded, cited, and scored.
          </h1>
          <p>
            <a className="button primary" href="/ask">
              Ask a question
            </a>
            <a
              className="button"
              href="https://github.com/Halomaster0/GTA-Housing-pipeline"
              rel="noopener"
            >
              View repo
            </a>
          </p>
        </div>
        <section className="panel" aria-labelledby="status-heading">
          <h2 id="status-heading">System status</h2>
          <div className="status">
            <span
              className={`dot ${allOk ? "live" : "stale"}`}
              aria-hidden="true"
            />
            <div>
              <div className="word">{allOk ? "Live" : "Degraded"}</div>
              <div className="sub">
                {feeds.ok} of {feeds.total} feeds reporting ok
              </div>
            </div>
          </div>
          <div className="metric">
            <div className="value gold">
              {formatInt(factTotals.fct_permits)}
            </div>
            <div className="label">
              Permits issued (gold layer) · last refresh {bronze.ingest_date}
            </div>
          </div>
          <div className="metric">
            <div className="value">
              {formatInt(factTotals.fct_applications)}
            </div>
            <div className="label">Applications tracked</div>
          </div>
        </section>
      </div>

      <h2>Pipeline status — per source</h2>
      {/* tabIndex on a scroll region is the design-plan §7 pattern (keyboard
          users must reach overflow content); jsx-a11y disagrees in general,
          the approved plan governs this site. The rule reports at the prop
          line, so this needs a disable/enable pair, not next-line. */}
      {/* eslint-disable jsx-a11y/no-noninteractive-tabindex -- design-plan §7 */}
      <div
        className="table-scroll"
        tabIndex={0}
        role="region"
        aria-label="Per-source ingest status, scrollable"
      >
        <table className="data">
          <caption>
            {bronze.sources.length} landed feeds, ingest date{" "}
            {bronze.ingest_date}. Rows landed vs rows the source reported.
          </caption>
          <thead>
            <tr>
              <th scope="col">Source</th>
              <th scope="col">Last ingested</th>
              <th scope="col" className="num">
                Rows landed
              </th>
              <th scope="col" className="num">
                Rows reported
              </th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            {bronze.sources.map((s) => (
              <tr key={s.source}>
                <td>{s.source}</td>
                <td>{s.ingest_date}</td>
                <td className="num">{formatInt(s.rows_landed)}</td>
                <td className="num">
                  {s.rows_reported === null
                    ? "metadata only"
                    : formatInt(s.rows_reported)}
                </td>
                <td>{s.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {/* eslint-enable jsx-a11y/no-noninteractive-tabindex */}
      </div>

      <h2>Municipalities by permits issued</h2>
      <figure className="figure-frame">
        {/* Build-time generated asset (scripts/build_map_svg.py, ADR-0009) —
            inlined so page CSS owns fills and both colour schemes. */}
        <div dangerouslySetInnerHTML={{ __html: mapSvg }} />
        <figcaption>
          Real municipal boundary geometry (Peel) and ward polygons
          (Toronto), filled by gold-layer permit volume:{" "}
          {Object.entries(muniNames)
            .map(
              ([code, name]) =>
                `${name} ${formatInt(permitsByMunicipality[code] ?? null)}`,
            )
            .join(" · ")}
          . Caledon has no permit feed (ADR-0004). Source:
          docs/measure-reconciliation.json, ingest date {bronze.ingest_date}.
        </figcaption>
      </figure>
    </>
  );
}
