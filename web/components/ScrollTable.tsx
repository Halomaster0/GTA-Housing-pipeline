import type { ReactNode } from "react";

/* Bordered, keyboard-reachable horizontal-scroll region for a data table
 * (design-plan §7). tabIndex on a scroll region is the approved pattern;
 * jsx-a11y disagrees in general, so the disable/enable pair lives here once
 * (the rule reports at the prop line, so next-line is not enough). */
export function ScrollTable({
  label,
  children,
  className = "table-scroll",
}: {
  label: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <>
      {/* eslint-disable jsx-a11y/no-noninteractive-tabindex -- design-plan §7 */}
      <div className={className} tabIndex={0} role="region" aria-label={label}>
        {children}
      </div>
      {/* eslint-enable jsx-a11y/no-noninteractive-tabindex */}
    </>
  );
}
