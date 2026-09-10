import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Evals",
  description:
    "Scored evaluation of the query layer — arriving with the Phase 4 harness.",
};

export default function Evals() {
  return (
    <>
      <h1>Evals — how we know it works</h1>
      <div className="empty">
        <p>
          <strong>No eval runs yet.</strong> The golden question set (about
          sixty questions across six buckets, including unanswerable ones the
          system must refuse) is written before anything it tests gets tuned.
          This page will render the scorecard live from committed result
          files — per-bucket scores plus the history, including the runs
          where scores went down.
        </p>
      </div>
      <h2>Methodology, in advance</h2>
      <p>
        Correctness, faithfulness, retrieval recall, refusal accuracy,
        latency, and cost per query. The harness runs in CI; a regression
        over five percent on correctness or faithfulness fails the build.
      </p>
    </>
  );
}
