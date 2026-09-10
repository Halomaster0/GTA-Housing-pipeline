# Director of Product & Frontend — design plan review

**Reviewer:** `director-product-frontend` · **Date:** 2026-09-10
**Under review:** `docs/design-plan.md` (Pass 1 + Pass 2 self-critique)
**New evidence since draft:** Caledon has no permit feed (confirmed gap);
all licences named (attribution strings must appear in footer + README).

## Checklist (per §5.17 — applied to the plan; no UI code exists yet)

- [x] Landing states what this is above the fold, no jargon — H1 two-sentence
  claim + live status panel side by side. Plan passes on paper.
- [x] `/ask` zero-setup with pre-loaded examples including a refusal — specified.
- [x] Rows + SQL + trace visible, not behind a toggle — two-column sticky layout
  (desktop) / stacked reading order (380px). Specified, including the
  captioned-scrollable-table solution for narrow screens.
- [x] `/evals` renders from committed result files with provenance captions —
  specified, including regressions shown, not hidden.
- [x] Mobile 380px wireframes for all five routes; keyboard path specified;
  focus rings with computed contrast; `prefers-reduced-motion` handled via the
  static step list. Accessibility floor is credible.
- [x] Loading (plotter-line, one motion moment) and error states designed;
  spend-ceiling styled neutral, not red. Correct.
- [x] Repo link on every page (header GitHub link + footer repo links).

## Conditions (one)

1. **Caledon on the map.** The landing map is specified as four municipal
   boundaries filled by permit volume — but Caledon has no permit feed. The map
   MUST render Caledon (and Peel-at-large, if shown) as an explicit no-data
   state, never as zero. Same rule as every other surface: absence rendered,
   never a plausible placeholder. `frontend-engineer` to note this in
   `web/styles/tokens.css` + component logic when Phase 4b starts.

## Notes for build

- Attribution strings (Toronto / Mississauga / Peel / StatCan / Brampton CC BY)
  must appear in the footer and README — licences now known, no longer blocked.
- Wireframe figures are illustrative placeholders; the plan already forbids
  shipping them as real. No action.
- The ninety-second test cannot pass until the site exists; it will be run with
  a real person at Gate 4b. No action now.

## Verdict: APPROVED with condition (1) — UI code unblocked for Phase 4b
