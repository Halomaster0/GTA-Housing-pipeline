import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard",
  description:
    "The published Power BI report — arriving with the funded Fabric serving layer.",
};

const PAGES: Array<{ n: number; title: string; answers: string }> = [
  { n: 1, title: "GTA Overview", answers: "Units and permits, this year vs prior." },
  {
    n: 2,
    title: "Municipal Comparison",
    answers: "Who is actually building, with per-capita views once census profiles land.",
  },
  {
    n: 3,
    title: "Pipeline Velocity",
    answers: "Application to permit timing, by municipality and use type.",
  },
  { n: 4, title: "Geography", answers: "Permit and application volume by ward." },
  {
    n: 5,
    title: "Data Quality and Freshness",
    answers: "Refresh dates, row counts, and known gaps, stated plainly.",
  },
];

export default function Dashboard() {
  return (
    <>
      <h1>Dashboard</h1>
      <div className="empty">
        <p>
          <strong>Not yet published.</strong> The report builds on the Fabric
          semantic model, which waits on the approved Fabric trial (see the
          data dictionary and report plan in the repo). The five pages are
          specified; the embed arrives with them.
        </p>
      </div>
      <h2>What each page will answer</h2>
      <ol>
        {PAGES.map((p) => (
          <li key={p.n}>
            <strong>{p.title}</strong> — {p.answers}
          </li>
        ))}
      </ol>
    </>
  );
}
