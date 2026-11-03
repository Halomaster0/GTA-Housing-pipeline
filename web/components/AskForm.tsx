"use client";

import { useState } from "react";

// Set at build time. Empty means no query service is connected, and the form says so.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

const EXAMPLES: string[] = [
  "How many permits were issued in Mississauga in 2023?",
  "Which Toronto wards have the most mixed-use applications?",
  "What will condo prices be in 2027?",
];

type Row = Record<string, unknown>;

type AskResult = {
  trace_id: string;
  answer: string;
  is_refusal: boolean;
  refusal_reason: string | null;
  sql: string | null;
  rows: Row[];
  row_count: number;
};

export function AskForm() {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<AskResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function ask(q: string) {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const resp = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      if (!resp.ok) {
        setError(`The query service returned ${resp.status}. Try again later.`);
        return;
      }
      setResult((await resp.json()) as AskResult);
    } catch {
      setError("The query service could not be reached.");
    } finally {
      setBusy(false);
    }
  }

  if (!API_URL) {
    return (
      <div className="empty">
        <p>
          <strong>The query service is not connected to this site yet.</strong>{" "}
          The planner, executor, and critic run on the backend; this page needs
          its address at build time.
        </p>
      </div>
    );
  }

  return (
    <>
      <form
        className="ask-form"
        onSubmit={(e) => {
          e.preventDefault();
          const q = question.trim();
          if (q) void ask(q);
        }}
      >
        <label htmlFor="question">Your question</label>
        <textarea
          id="question"
          value={question}
          maxLength={500}
          rows={3}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button type="submit" className="button primary" disabled={busy || !question.trim()}>
          {busy ? "Working…" : "Ask"}
        </button>
      </form>

      <h2>Examples</h2>
      <ul>
        {EXAMPLES.map((q) => (
          <li key={q}>
            <button type="button" onClick={() => { setQuestion(q); void ask(q); }}>
              {q}
            </button>
          </li>
        ))}
      </ul>

      {error && <p role="alert">{error}</p>}

      {result && (
        <section aria-live="polite">
          <h2>Answer</h2>
          <p>{result.answer}</p>
          {result.is_refusal && result.refusal_reason && (
            <p>
              <strong>Refused:</strong> {result.refusal_reason}
            </p>
          )}
          {result.sql && (
            <>
              <h3>SQL</h3>
              <pre>
                <code>{result.sql}</code>
              </pre>
            </>
          )}
          {result.rows.length > 0 && (
            <>
              <h3>
                Rows ({result.row_count}
                {result.row_count > result.rows.length ? `, first ${result.rows.length} shown` : ""})
              </h3>
              <div className="scroll">
                <table>
                  <caption>Rows returned by the query</caption>
                  <thead>
                    <tr>
                      {Object.keys(result.rows[0]).map((c) => (
                        <th key={c}>{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.rows.slice(0, 20).map((row, i) => (
                      <tr key={i}>
                        {Object.keys(result.rows[0]).map((c) => (
                          <td key={c}>{String(row[c] ?? "")}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
          <p>
            <small>Trace: {result.trace_id}</small>
          </p>
        </section>
      )}
    </>
  );
}
