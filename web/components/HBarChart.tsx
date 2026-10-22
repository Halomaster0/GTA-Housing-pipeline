/* Sorted horizontal bar chart in hand-written SVG (design-plan Pass 2: no
 * charting library). Every row carries its value as text, so colour is never
 * the only encoding. Label above the bar, bar beneath, optional detail line:
 * this layout compresses to a 380px phone without shrinking the type. */

export interface HBarItem {
  label: string;
  value: number;
  valueText: string;
  detail?: string;
}

const W = 360;
const ROW = 46;
const ROW_DETAIL = 64;

export function HBarChart({
  items,
  ariaLabel,
}: {
  items: HBarItem[];
  ariaLabel: string;
}) {
  let y = 4;
  const rows = items.map((it) => {
    const top = y;
    y += it.detail ? ROW_DETAIL : ROW;
    return { ...it, top };
  });
  const height = y + 2;
  const max = Math.max(...items.map((i) => i.value), 0);

  return (
    <svg
      className="chart-svg narrow"
      viewBox={`0 0 ${W} ${height}`}
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label={ariaLabel}
    >
      {rows.map((r) => {
        const w =
          max > 0 && r.value > 0 ? Math.max(1.5, (r.value / max) * W) : 0;
        return (
          <g key={r.label}>
            <text x={0} y={r.top + 16} className="chart-label">
              {r.label}
            </text>
            <text x={W} y={r.top + 16} textAnchor="end" className="chart-num">
              {r.valueText}
            </text>
            {w > 0 ? (
              <rect
                x={0}
                y={r.top + 23}
                width={w}
                height={12}
                className="bar-fill"
              />
            ) : null}
            {r.detail ? (
              <text x={0} y={r.top + 54} className="chart-detail">
                {r.detail}
              </text>
            ) : null}
          </g>
        );
      })}
    </svg>
  );
}
