import type { Metadata } from "next";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

export const metadata: Metadata = {
  title: "Evals",
  description:
    "Scored evaluation of the query layer, rendered from the committed result files.",
};

type Scores = {
  correctness: number;
  faithfulness: number;
  refusal_accuracy: number | null;
};

type Run = {
  run_date: string;
  git_sha: string;
  faithfulness_metric_version?: number;
  overall: Scores & { total_questions: number };
  by_bucket: Record<
    string,
    Scores & { n: number; p50_latency_ms: number; p95_latency_ms: number }
  >;
};

// Built from the repo root's evals/results, which is in the Vercel checkout
// next to web/. Runs are sorted by date, then metric version, so the last one
// is the current scorecard.
const RESULTS_DIR = join(process.cwd(), "..", "evals", "results");

function loadRuns(): Run[] {
  return readdirSync(RESULTS_DIR)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(readFileSync(join(RESULTS_DIR, f), "utf-8")) as Run)
    .sort(
      (a, b) =>
        a.run_date.localeCompare(b.run_date) ||
        (a.faithfulness_metric_version ?? 0) - (b.faithfulness_metric_version ?? 0),
    );
}

const pct = (x: number | null) => (x === null ? "n/a" : `${(x * 100).toFixed(1)}%`);
const ms = (x: number) => `${Math.round(x).toLocaleString("en-CA")} ms`;
const metric = (run: Run) =>
  run.faithfulness_metric_version === undefined
    ? "v1 (no version recorded)"
    : `v${run.faithfulness_metric_version}`;

export default function Evals() {
  const runs = loadRuns();
  const latest = runs[runs.length - 1];

  return (
    <>
      <h1>Evals — how we know it works</h1>
      <p>
        Latest run: {latest.run_date}, commit <code>{latest.git_sha}</code>,
        faithfulness {metric(latest)}, {latest.overall.total_questions} golden
        questions.
      </p>

      <h2>Overall</h2>
      <table>
        <caption>Overall scores, latest run</caption>
        <thead>
          <tr>
            <th>Correctness</th>
            <th>Faithfulness</th>
            <th>Refusal accuracy</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{pct(latest.overall.correctness)}</td>
            <td>{pct(latest.overall.faithfulness)}</td>
            <td>{pct(latest.overall.refusal_accuracy)}</td>
          </tr>
        </tbody>
      </table>

      <h2>By bucket</h2>
      <table>
        <caption>Scores by question bucket, latest run</caption>
        <thead>
          <tr>
            <th>Bucket</th>
            <th>Questions</th>
            <th>Correctness</th>
            <th>Faithfulness</th>
            <th>Refusal accuracy</th>
            <th>p50 latency</th>
            <th>p95 latency</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(latest.by_bucket).map(([name, b]) => (
            <tr key={name}>
              <td>{name.replace(/_/g, " ")}</td>
              <td>{b.n}</td>
              <td>{pct(b.correctness)}</td>
              <td>{pct(b.faithfulness)}</td>
              <td>{pct(b.refusal_accuracy)}</td>
              <td>{ms(b.p50_latency_ms)}</td>
              <td>{ms(b.p95_latency_ms)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>History</h2>
      <p>
        Every committed run, including the ones where scores went down. Scores
        from different faithfulness metric versions are not directly comparable.
      </p>
      <table>
        <caption>Every committed eval run</caption>
        <thead>
          <tr>
            <th>Date</th>
            <th>Commit</th>
            <th>Faithfulness metric</th>
            <th>Correctness</th>
            <th>Faithfulness</th>
            <th>Refusal accuracy</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={`${run.run_date}-${run.git_sha}-${run.faithfulness_metric_version ?? 1}`}>
              <td>{run.run_date}</td>
              <td>
                <code>{run.git_sha}</code>
              </td>
              <td>{metric(run)}</td>
              <td>{pct(run.overall.correctness)}</td>
              <td>{pct(run.overall.faithfulness)}</td>
              <td>{pct(run.overall.refusal_accuracy)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Methodology</h2>
      <p>
        Correctness, faithfulness, refusal accuracy, and latency per bucket. The
        harness runs locally against the September warehouse. CI reports the
        eval step as skipped, because it needs data that is not in the
        repository and an API key. Nothing currently fails the build on a score
        drop.
      </p>
    </>
  );
}
