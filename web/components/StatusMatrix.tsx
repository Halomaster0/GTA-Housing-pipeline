import { ScrollTable } from "./ScrollTable";
import { formatInt, municipalityName } from "../lib/measures";

export interface StatusCount {
  municipality: string;
  status: string;
  count: number;
}

/* Status by municipality as a real table. A status a municipality has no rows
 * for reads "none recorded", never a zero: the feed simply has no such state. */
export function StatusMatrix({
  rows,
  codes,
  caption,
  scrollLabel,
  noun,
}: {
  rows: StatusCount[];
  codes: string[];
  caption: string;
  scrollLabel: string;
  noun: string;
}) {
  const cell = new Map<string, number>();
  const statusTotal = new Map<string, number>();
  const codeTotal = new Map<string, number>();
  for (const r of rows) {
    cell.set(`${r.municipality}|${r.status}`, r.count);
    statusTotal.set(r.status, (statusTotal.get(r.status) ?? 0) + r.count);
    codeTotal.set(
      r.municipality,
      (codeTotal.get(r.municipality) ?? 0) + r.count,
    );
  }
  const statuses = [...statusTotal.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([s]) => s);
  const grand = [...statusTotal.values()].reduce((a, b) => a + b, 0);

  return (
    <ScrollTable label={scrollLabel}>
      <table className="data">
        <caption>{caption}</caption>
        <thead>
          <tr>
            <th scope="col">Status</th>
            {codes.map((c) => (
              <th scope="col" className="num" key={c}>
                {municipalityName(c)}
              </th>
            ))}
            <th scope="col" className="num">
              All {noun}
            </th>
          </tr>
        </thead>
        <tbody>
          {statuses.map((s) => (
            <tr key={s}>
              <th scope="row">
                <code>{s}</code>
              </th>
              {codes.map((c) => {
                const v = cell.get(`${c}|${s}`);
                return v === undefined ? (
                  <td className="num na" key={c}>
                    none recorded
                  </td>
                ) : (
                  <td className="num" key={c}>
                    {formatInt(v)}
                  </td>
                );
              })}
              <td className="num">{formatInt(statusTotal.get(s) ?? null)}</td>
            </tr>
          ))}
          <tr>
            <th scope="row">All statuses</th>
            {codes.map((c) => (
              <td className="num" key={c}>
                {formatInt(codeTotal.get(c) ?? null)}
              </td>
            ))}
            <td className="num">{formatInt(grand)}</td>
          </tr>
        </tbody>
      </table>
    </ScrollTable>
  );
}
