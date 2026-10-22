import type { ReactNode } from "react";
import { provenanceLine } from "../lib/measures";

/* Chart frame (design-plan §5): 1px border, a caption line beneath the chart,
 * and a provenance line naming the source file, git sha, and as-of date.
 * An SVG is never the only way to read the data, so every frame carries the
 * same figures as a real table in a disclosure. */
export function ChartFrame({
  id,
  title,
  caption,
  children,
  table,
  tableSummary,
  tableOpen = false,
}: {
  id: string;
  title: string;
  caption: ReactNode;
  children: ReactNode;
  table: ReactNode;
  tableSummary: string;
  tableOpen?: boolean;
}) {
  return (
    <div className="chart-frame">
      <h3 id={`${id}-title`}>{title}</h3>
      <figure className="chart-figure" aria-labelledby={`${id}-title`}>
        {children}
        <figcaption>
          <p>{caption}</p>
          <p className="provenance">{provenanceLine()}</p>
        </figcaption>
      </figure>
      <details className="chart-data" open={tableOpen}>
        <summary>{tableSummary}</summary>
        {table}
      </details>
    </div>
  );
}
