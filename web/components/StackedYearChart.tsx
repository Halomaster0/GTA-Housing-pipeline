import { ScrollTable } from "./ScrollTable";
import {
  asOfYear,
  formatInt,
  municipalityName,
  type PermitsIssuedRow,
} from "../lib/measures";

/* Stacked bar of permits issued per calendar year, by municipality, in
 * hand-written SVG. Two honesty rules drive the drawing:
 *  - A municipality with no rows for a year is NOT drawn as a zero. Its absence
 *    is marked with a coverage bracket under the axis and a divider where the
 *    series begins.
 *  - The as-of year is partial and is drawn with a dashed outline and labelled.
 * Series are told apart by fill treatment (solid, half-tone, hatched) and by
 * direct text labels at the right edge, never by colour alone. */

const W = 800;
const H = 440;
const M = { l: 62, r: 108, t: 52, b: 92 };
const PLOT_W = W - M.l - M.r;
const PLOT_H = H - M.t - M.b;

function niceStep(raw: number): number {
  const pow = Math.pow(10, Math.floor(Math.log10(raw)));
  const frac = raw / pow;
  const nice = frac <= 1 ? 1 : frac <= 2 ? 2 : frac <= 5 ? 5 : 10;
  return nice * pow;
}

function compact(n: number): string {
  return `${(n / 1000).toFixed(1)}k`;
}

interface Model {
  years: number[];
  value: (code: string, year: number) => number | undefined;
  first: Record<string, number>;
  last: Record<string, number>;
}

function buildModel(rows: PermitsIssuedRow[]): Model {
  const map = new Map<string, number>();
  const first: Record<string, number> = {};
  const last: Record<string, number> = {};
  for (const r of rows) {
    map.set(`${r.municipality}|${r.year}`, r.permits_issued);
    if (first[r.municipality] === undefined || r.year < first[r.municipality]) {
      first[r.municipality] = r.year;
    }
    if (last[r.municipality] === undefined || r.year > last[r.municipality]) {
      last[r.municipality] = r.year;
    }
  }
  const all = rows.map((r) => r.year);
  const min = Math.min(...all);
  const max = Math.max(...all);
  const years = Array.from({ length: max - min + 1 }, (_, i) => min + i);
  return { years, value: (c, y) => map.get(`${c}|${y}`), first, last };
}

function describe(rows: PermitsIssuedRow[], order: string[], m: Model): string {
  const parts = order.map((code) => {
    const own = rows.filter((r) => r.municipality === code);
    const lo = own.reduce((a, r) =>
      r.permits_issued < a.permits_issued ? r : a,
    );
    const hi = own.reduce((a, r) =>
      r.permits_issued > a.permits_issued ? r : a,
    );
    return `${municipalityName(code)}, ${m.first[code]} to ${m.last[code]}: lowest ${formatInt(lo.permits_issued)} in ${lo.year}, highest ${formatInt(hi.permits_issued)} in ${hi.year}.`;
  });
  const years = m.years;
  const late = order
    .filter((c) => m.first[c] > years[0])
    .map((c) => `${municipalityName(c)} has no data before ${m.first[c]}.`);
  return (
    `Stacked bar chart of permits issued per calendar year, ${years[0]} to ${years[years.length - 1]}. ` +
    `${parts.join(" ")} ${late.join(" ")} ` +
    `${asOfYear} is a partial year. Every value is in the data table below the chart.`
  );
}

export function StackedYearChart({
  rows,
  order,
}: {
  rows: PermitsIssuedRow[];
  order: string[];
}) {
  const m = buildModel(rows);
  const n = m.years.length;
  const slot = PLOT_W / n;
  const barW = Math.min(28, slot * 0.7);
  const x0 = (i: number) => M.l + i * slot;

  const totals = m.years.map((y) =>
    order.reduce((a, c) => a + (m.value(c, y) ?? 0), 0),
  );
  const step = niceStep(Math.max(...totals) / 6);
  const yMax = Math.ceil(Math.max(...totals) / step) * step;
  const ticks: number[] = [];
  for (let t = 0; t <= yMax; t += step) ticks.push(t);
  const ys = (v: number) => M.t + PLOT_H - (v / yMax) * PLOT_H;
  const baseY = M.t + PLOT_H;

  // Right-edge direct labels, nudged apart so adjacent short segments stay legible.
  const lastYear = m.years[n - 1];
  let cum = 0;
  const labels = order
    .map((c, idx) => {
      const v = m.value(c, lastYear);
      if (v === undefined) return null;
      const mid = ys(cum + v / 2);
      cum += v;
      return { code: c, idx, y: mid };
    })
    .filter((l): l is { code: string; idx: number; y: number } => l !== null)
    .sort((a, b) => a.y - b.y);
  for (let i = 1; i < labels.length; i++) {
    if (labels[i].y - labels[i - 1].y < 15) labels[i].y = labels[i - 1].y + 15;
  }

  const late = order.filter((c) => m.first[c] > m.years[0]);

  return (
    <>
      <p className="scroll-hint">
        This chart scrolls sideways so every year stays legible.
      </p>
      <ScrollTable
        className="chart-scroll"
        label="Permits issued by year chart, scrollable"
      >
        <svg
          className="chart-svg wide"
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="xMidYMid meet"
          role="img"
          aria-label={describe(rows, order, m)}
        >
          <defs>
            <pattern
              id="year-hatch"
              width="6"
              height="6"
              patternUnits="userSpaceOnUse"
              patternTransform="rotate(45)"
            >
              <rect width="6" height="6" className="hatch-bg" />
              <line x1="0" y1="0" x2="0" y2="6" className="hatch-line" />
            </pattern>
          </defs>

          <text x={0} y={16} className="chart-label">
            Permits issued per year
          </text>

          {ticks.map((t) => (
            <g key={t}>
              <line
                x1={M.l}
                x2={M.l + PLOT_W}
                y1={ys(t)}
                y2={ys(t)}
                className="chart-grid"
              />
              <text
                x={M.l - 8}
                y={ys(t) + 4}
                textAnchor="end"
                className="chart-num tick"
              >
                {formatInt(t)}
              </text>
            </g>
          ))}

          {m.years.map((y, i) => {
            const bx = x0(i) + (slot - barW) / 2;
            const partial = y === asOfYear;
            let acc = 0;
            return (
              <g key={y}>
                {order.map((c, idx) => {
                  const v = m.value(c, y);
                  if (v === undefined) return null;
                  const top = ys(acc + v);
                  const h = ys(acc) - top;
                  acc += v;
                  return (
                    <rect
                      key={c}
                      x={bx}
                      y={top}
                      width={barW}
                      height={h}
                      className={`seg series-${idx}${partial ? " partial" : ""}`}
                      fill={idx >= 2 ? "url(#year-hatch)" : undefined}
                    />
                  );
                })}
                <text
                  x={x0(i) + slot / 2}
                  y={ys(totals[i]) - 5}
                  textAnchor="middle"
                  className="chart-num tick"
                >
                  {compact(totals[i])}
                </text>
                <text
                  x={x0(i) + slot / 2}
                  y={baseY + 16}
                  textAnchor="middle"
                  className="chart-num tick"
                >
                  {y}
                </text>
                {partial ? (
                  <text
                    x={x0(i) + slot / 2}
                    y={baseY + 30}
                    textAnchor="middle"
                    className="chart-detail"
                  >
                    partial
                  </text>
                ) : null}
              </g>
            );
          })}

          <line
            x1={M.l}
            x2={M.l + PLOT_W}
            y1={baseY}
            y2={baseY}
            className="chart-axis"
          />

          {/* Where a municipality's series begins: a divider and a labelled bracket,
            so the missing years read as "no data", not as zero. */}
          {late.map((c) => {
            const startIdx = m.first[c] - m.years[0];
            const dx = x0(startIdx);
            const bracketY = baseY + 52;
            return (
              <g key={c}>
                <line
                  x1={dx}
                  x2={dx}
                  y1={28}
                  y2={baseY}
                  className="chart-divider"
                />
                <text x={dx + 6} y={24} className="chart-detail">
                  {`${municipalityName(c)} series begins in ${m.first[c]}`}
                </text>
                <line
                  x1={M.l + 4}
                  x2={dx - 4}
                  y1={bracketY}
                  y2={bracketY}
                  className="chart-axis"
                />
                <line
                  x1={M.l + 4}
                  x2={M.l + 4}
                  y1={bracketY - 5}
                  y2={bracketY + 5}
                  className="chart-axis"
                />
                <line
                  x1={dx - 4}
                  x2={dx - 4}
                  y1={bracketY - 5}
                  y2={bracketY + 5}
                  className="chart-axis"
                />
                <text
                  x={(M.l + dx) / 2}
                  y={bracketY + 20}
                  textAnchor="middle"
                  className="chart-detail"
                >
                  {`${municipalityName(c)}: no data before ${m.first[c]} (not zero)`}
                </text>
              </g>
            );
          })}

          {labels.map((l) => (
            <text
              key={l.code}
              x={M.l + PLOT_W + 10}
              y={l.y + 4}
              className="chart-label"
            >
              {municipalityName(l.code)}
            </text>
          ))}
        </svg>
      </ScrollTable>
    </>
  );
}

/* The same figures as the chart, as a real table. */
export function YearTable({
  rows,
  order,
}: {
  rows: PermitsIssuedRow[];
  order: string[];
}) {
  const m = buildModel(rows);
  return (
    <ScrollTable label="Permits issued by year, by municipality, scrollable">
      <table className="data">
        <caption>
          {m.years.length} calendar years, {order.length} municipalities. No
          data means the municipality has no records in this series for that
          year; it is not a zero. {asOfYear} is a partial year.
        </caption>
        <thead>
          <tr>
            <th scope="col">Year</th>
            {order.map((c) => (
              <th scope="col" className="num" key={c}>
                {municipalityName(c)}
              </th>
            ))}
            <th scope="col" className="num">
              Total of municipalities with data
            </th>
          </tr>
        </thead>
        <tbody>
          {m.years.map((y) => {
            const present = order
              .map((c) => m.value(c, y))
              .filter((v): v is number => v !== undefined);
            return (
              <tr key={y}>
                <th scope="row">{y === asOfYear ? `${y} (partial)` : y}</th>
                {order.map((c) => {
                  const v = m.value(c, y);
                  return v === undefined ? (
                    <td className="num na" key={c}>
                      no data
                    </td>
                  ) : (
                    <td className="num" key={c}>
                      {formatInt(v)}
                    </td>
                  );
                })}
                <td className="num">
                  {formatInt(present.reduce((a, b) => a + b, 0))}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </ScrollTable>
  );
}
