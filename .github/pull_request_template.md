<!--
Thanks for contributing. Fill out every section — a PR that skips the evidence
section will be sent back before review, not approved on trust. Delete the
Director checklists that don't apply to this PR; keep only the ones relevant
to what changed.
-->

## What changed and why

<!-- What does this PR do, and why does it need to happen? Link the problem, not just the fix. -->

## Linked issue

Closes #

## Phase and gate this advances

<!-- e.g. "Phase 1 — source verification, contributes to Gate 1 criterion: every source confirmed live." See docs/build-plan.md §6. -->

## Evidence

> "An agent's assertion is not evidence." — `docs/build-plan.md` §5.26

Paste actual command output below. A description of what you expect a command to do is not evidence; the output of actually running it is.

```
$ <command you ran>
<pasted output>
```

## Data-truth checklist

- [ ] This PR adds no new number to any doc, README, or UI, **or**
- [ ] Every new number added traces to a committed script and a committed output file (link both here):
  - Script: `path/to/script`
  - Output: `path/to/output`
- [ ] No "improved X by Y%" claim without a committed before-measurement
- [ ] Any eval score referenced is the score from the last CI run, not a hand-picked best run

## Secrets checklist

- [ ] No API key, token, credential, or connection string is present anywhere in this diff (checked the actual diff, not just the file names)
- [ ] `.env.example` only — no real `.env` file committed
- [ ] If a secret was ever committed in this branch's history (even if later removed), it has been rotated **and** the history has been rewritten, and this is called out explicitly in this PR description

## Reviewing Director's checklist

<!-- Keep only the section(s) that match what this PR touches. Delete the rest. -->

<details>
<summary>Director of Data Engineering — ingestion, transform, warehouse modelling (§5.2)</summary>

- [ ] Ingest is idempotent — rerunning does not duplicate rows
- [ ] Raw layer is immutable and partitioned by `ingest_date`
- [ ] Every silver table has a declared grain, documented in the model file header
- [ ] Primary keys tested for uniqueness and non-null
- [ ] Timezone handling explicit (all timestamps stored UTC, displayed America/Toronto)
- [ ] Currency, area units, and geography CRS conformed and documented
- [ ] Gold SQL is hand-written and readable — no 400-line CTE with no comments
- [ ] Schema change from source would fail loudly, not silently

</details>

<details>
<summary>Director of Platform — CI/CD, orchestration, reproducibility (§5.7)</summary>

- [ ] `make setup && make pipeline && make test` works from a clean clone
- [ ] No secrets in the repo; `.env.example` complete
- [ ] CI runs ingest (against fixtures), transform, data tests, and eval on every PR
- [ ] Fabric artifacts are defined as code or documented step-by-step with screenshots
- [ ] Cost of any cloud resource is recorded before it's provisioned

</details>

<details>
<summary>Director of AI — RAG, orchestration, evaluation (§5.10)</summary>

- [ ] Every LLM answer is traceable to specific retrieved rows, returned with the answer
- [ ] SQL execution is read-only and against a restricted role — no LLM-generated DDL/DML, ever
- [ ] The system refuses cleanly when the data can't answer the question — measured as a metric
- [ ] Retrieval is evaluated separately from generation
- [ ] No prompt is more than one file away from its eval cases
- [ ] Token cost per query is logged

</details>

<details>
<summary>Director of Analytics — semantic model, Power BI, narrative (§5.14)</summary>

- [ ] Every measure has a definition in the data dictionary
- [ ] Report answers questions, doesn't just display columns
- [ ] Filters, drill-through, and cross-filter behaviour deliberate, not default
- [ ] Accessible colour contrast; no red/green-only encoding
- [ ] Every number on the dashboard reconciles to a gold-layer query

</details>

<details>
<summary>Director of Product & Frontend — web app, API contract, visitor experience (§5.17)</summary>

- [ ] Landing page states what this is in plain language above the fold — no jargon, no marketing
- [ ] The `/ask` console works on first visit with zero setup and has example questions pre-loaded
- [ ] Every AI answer displays its rows, its SQL, and a link to the trace — visibly, not behind a toggle
- [ ] `/evals` renders from committed result files, not hardcoded numbers
- [ ] Works on mobile; keyboard navigable; visible focus states; `prefers-reduced-motion` respected
- [ ] Loading and error states are designed, not spinners and stack traces
- [ ] Repo link is present on every page

</details>
