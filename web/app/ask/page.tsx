import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Ask the warehouse",
  description:
    "Plain-English questions against the gold layer — arriving with the Phase 4 query layer.",
};

const EXAMPLES: string[] = [
  "How many residential permits did Mississauga issue in 2023?",
  "Which Toronto wards have the most mixed-use applications?",
  "What will condo prices be in 2027? — the system must refuse this",
];

export default function Ask() {
  return (
    <>
      <h1>Ask the warehouse</h1>
      <div className="empty">
        <p>
          <strong>Not yet built.</strong> The query layer (planner, executor,
          critic, eval harness) is Phase 4 work and needs an API key plus a
          spend ceiling first. This route will carry the question box, the
          answer with its rows, the executed SQL, and the trace link — all
          visible at once, with no toggle.
        </p>
      </div>
      <h2>Questions it will answer on day one</h2>
      <ul>
        {EXAMPLES.map((q) => (
          <li key={q}>{q}</li>
        ))}
      </ul>
    </>
  );
}
