import type { Metadata } from "next";
import { AskForm } from "../../components/AskForm";

export const metadata: Metadata = {
  title: "Ask the warehouse",
  description:
    "Plain-English questions against the gold layer, answered with the SQL and rows that produced them.",
};

export default function Ask() {
  return (
    <>
      <h1>Ask the warehouse</h1>
      <p>
        Ask a question about permits, applications, and municipalities. The answer
        comes with the SQL it ran and the rows it used. Questions the data cannot
        answer are refused, with the reason.
      </p>
      <AskForm />
    </>
  );
}
