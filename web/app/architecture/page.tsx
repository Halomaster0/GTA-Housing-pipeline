import type { Metadata } from "next";
import { REPO_URL } from "../../lib/measures";

export const metadata: Metadata = {
  title: "Architecture",
  description:
    "How the GTA Housing Pipeline is built: sources, layers, serving, and the decisions behind them.",
};

const STAGES: Array<{ stage: string; detail: string }> = [
  {
    stage: "Sources",
    detail: "Toronto CKAN, Peel/Mississauga/Brampton ArcGIS Hub, StatCan. Official APIs only.",
  },
  {
    stage: "Bronze",
    detail: "Raw landed parquet, immutable, partitioned by ingest date. 20 feeds, ~940k rows.",
  },
  {
    stage: "Silver",
    detail: "Typed, deduped, PII-dropped entities. Every table declares its grain.",
  },
  {
    stage: "Gold",
    detail: "Hand-written star schema: fct_permits (827,919), fct_applications (21,658), five dimensions.",
  },
  {
    stage: "Serving",
    detail: "Parquet export plus a pinned measure library. Fabric lakehouse when the trial is approved.",
  },
  {
    stage: "Web app",
    detail: "This site: a static export over committed artifacts. No server, no placeholders.",
  },
];

export default function Architecture() {
  return (
    <>
      <h1>Architecture</h1>
      <ol className="pipeline-diagram">
        {STAGES.map((s) => (
          <li key={s.stage}>
            <div className="stage">{s.stage}</div>
            <div className="detail">{s.detail}</div>
          </li>
        ))}
      </ol>
      <div className="prose">
        <h2 id="sources">Sources</h2>
        <p>
          Four municipal open-data families feed the pipeline: Toronto&apos;s
          CKAN portal (building permits, development applications, wards),
          the Peel/Mississauga/Brampton ArcGIS Hub services, and Statistics
          Canada product tables for control totals. Every source was verified
          live before any ingestion code was written, and each carries a
          named licence permitting public reuse (see ADR-0004 and the sources
          register).
        </p>
        <h2 id="layers">Bronze, silver, gold</h2>
        <p>
          Bronze lands raw responses untouched so the evidence survives any
          modelling mistake. Silver cleans and conforms: composite row keys
          proven per feed, Toronto&apos;s per-address application rows
          collapsed to file grain, PII columns dropped at the boundary. Gold
          is hand-written SQL, not generated — conforming four
          municipalities&apos; different definitions of application, unit,
          and status is a modelling judgement, recorded rule by rule in the
          conformance matrix (see ADR-0003 through ADR-0007).
        </p>
        <h2 id="truth">Truth discipline</h2>
        <p>
          Every number on this site is read at build time from a committed
          artifact produced by a committed script. No projected metrics, no
          illustrative figures. Where the data cannot answer yet — per-capita
          measures, application-to-permit timing — the page says so instead
          of printing a zero.
        </p>
        <h2 id="decisions">Decision records</h2>
        <p>
          Choices a future reader would ask &ldquo;why?&rdquo; about live in{" "}
          <a href={`${REPO_URL}/tree/main/docs/decisions`} rel="noopener">
            docs/decisions
          </a>
          : unit-count basis, Peel framing and Caledon scope, application
          grain, real-key-only linkage, ward versioning, deferred Fabric
          serving, and this static-export web app.
        </p>
      </div>
    </>
  );
}
