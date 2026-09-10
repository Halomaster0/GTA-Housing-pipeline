# ADR-0001: Tooling and CI baseline

Status: Accepted · Date: 2026-09-10 · Decider: `cicd-engineer` · Reviewed by: (pending Director of Platform review)

## Context

Phase 1, day 1. The repository skeleton exists (`src/`, `models/`, `tests/`,
`evals/`, `fixtures/`, `docs/`, etc.) but contains no application code —
ingestion is Phase 2, transform is Phase 2, the AI layer is Phase 4, the web
app is Phase 4b. `cicd-engineer` still has to stand up a real dependency
manifest, a Makefile, pre-commit hooks, and four green GitHub Actions
workflows against a repository that legitimately has almost nothing in it
yet. Two other agents (`oss-maintainer`, `source-scout`) are working
concurrently on disjoint file sets in the same repo, so anything this ADR
decides has to compose with work this agent cannot see yet (in particular:
`scripts/verify_sources.py` may or may not exist at any given time until
Phase 1 closes).

Per docs/build-plan.md §0.1, the repo is public from the first commit. A red
CI badge on day one is worse than no badge, but a fake-green badge (a stub
that reports success for work that failed, or a test that always passes) is
worse than either — it teaches nobody to trust the badge.

## Decisions

### 1. `uv`, not `pip-tools`

`uv` does venv creation, dependency resolution, lockfile generation
(`uv.lock`), and running commands (`uv run`) in one tool, with a Rust-speed
resolver. `pip-tools` (`pip-compile` + `pip-sync`) needs a separate venv step
and a separate runner, and is noticeably slower to resolve. Given this
project's CI runs many small jobs (lint, typecheck, unit, data, eval,
verify-sources, pipeline) and cost/speed of CI is itself a stated constraint
(R5, R8 in docs/build-plan.md §9), the single fast tool wins. `uv` also
manages the pinned Python interpreter itself (`requires-python = "==3.11.*"`),
removing a class of "works on my machine" drift.

`uv.lock` is committed. Every pin in `pyproject.toml` was verified by running
`uv lock --python 3.11` against live PyPI on 2026-09-10 (see Validation
below) — none of the version numbers were guessed.

**Non-package project.** `[tool.uv] package = false` is set because this repo
is an application/pipeline, not a library meant to be built into a wheel and
published. There is no `gta_housing_pipeline/__init__.py` for a build backend
to discover; `src/ingest`, `src/transform`, etc. are run in place (`python -m
src.ingest`, always from the repo root, or via `uv run`). Setting
`package = false` tells uv to treat `pyproject.toml` purely as a dependency
manifest and skip trying to build/install "the project" as its own package —
without this, `uv sync` would fail looking for something to wheel.

### 2. `ruff`, not `black` + `flake8` (+ `isort`)

One tool instead of three, one config block instead of three, one CI step
instead of three (or one step running three separate binaries). `ruff` covers
formatting (replaces `black`), linting (replaces `flake8`), and import sorting
(replaces `isort`, via the `I` rule set) at Rust speed. The rule selection
(`E`, `F`, `I`, `UP`, `B`, `C4`, `SIM`) is deliberately narrow for day one —
correctness and real-bug rules (bugbear, comprehensions, simplify), pyflakes,
import order, and pycodestyle basics — without turning on the hundreds of
stylistic rule families that would generate noise against code that does not
exist yet. Expand the `select` list as real modules land and specific rule
families prove useful; do not turn everything on at once.

### 3. `structlog`, not stdlib `logging`

Two reasons this project specifically needs structured logs, not just "nicer"
ones:

- Phase 4's orchestration runtime persists a full trace per query
  (`traces/{trace_id}.json` — docs/build-plan.md §5.12) and a per-query cost
  log (`docs/cost-log.md` — §5.22). Both want structured, machine-parseable
  events (stage, latency, cost, trace_id as fields, not string-interpolated
  into a message), which is `structlog`'s whole design, not something bolted
  onto stdlib `logging` after the fact.
- `structlog` wraps stdlib `logging` rather than replacing it, so ingestion
  and transform code (Phase 2, no tracing concerns) can use the same logger
  without adopting AI-layer-specific conventions early.

The cost is one more dependency and one more thing to configure
(`src/common`, Phase 2) versus "just import logging" — accepted, because the
trace/cost requirements are already committed to in the build plan, not
speculative.

### 4. `gitleaks`, not `detect-secrets`

Both are reasonable. `gitleaks` was chosen because it needs no baseline file:
`detect-secrets` requires generating and periodically auditing a
`.secrets.baseline` file to suppress known-false-positives, which is real
ongoing maintenance for a solo-maintained repo. `gitleaks` runs
pattern+entropy detection against the diff with no state to keep in sync. For
docs/build-plan.md §0.1's "no secrets ever committed, not even briefly" and
risk R9 (`.pre-commit-config.yaml`), zero-config beats slightly more precise
but stateful. Pinned to `v8.30.1` (verified against the live tag list, not
guessed).

### 5. `commitlint.config.js`, not `.commitlintrc.yaml`

`commitlint`'s own resolution order tries `commitlint.config.js` before any rc
file, so this file needs no `--config` flag wherever `commitlint` runs — the
pre-commit hook, a future CI step, or a contributor running it by hand all
just work. This introduces no new language to the stack: the repo already
carries Node/JS for the Phase 4b Next.js app (`web/`), so a `.js` config file
is not a new toolchain, just an early use of one already committed to in
§2 of the build plan.

### 6. mypy: strict on `src/`, global `ignore_missing_imports`

`strict = true` is turned on from day one specifically because there is no
code yet to migrate — every module written from Phase 2 onward starts strict,
rather than the far more common (and far more painful) path of turning
strict mode on after a codebase already exists. `ignore_missing_imports` is
set globally (not per-module) purely because there is nothing to enumerate: a
per-module `[[tool.mypy.overrides]]` list naming specific untyped
dependencies is more precise, but with zero imports in the codebase there is
no real list to write yet. Revisit this as a per-module override list once
`src/ingest` and `src/transform` have actual third-party imports — a global
blanket ignore is the right call for an empty tree, not for a grown one.

### 7. Keeping CI honestly green while most of the pipeline is unbuilt

The hard constraint: all four workflows must be green today, and none of them
may fake a pass. The pattern applied everywhere:

- **Work that is simply not started yet** (`ingest`, `transform`, `eval`,
  `report` in the Makefile; the pipeline.yml steps; the eval-fast-subset job
  in pr.yml) prints an explicit `not implemented -- Phase N` message naming
  where it lands, and exits 0. This is not a stub that pretends to succeed at
  something — it is an honest statement that the work has not started, which
  is true today and will stop being printed the moment the real
  implementation exists.
- **Work whose infrastructure exists but has nothing to check yet** is
  handled differently, because it is a real tool reporting a real (if empty)
  result, not a phase that hasn't started. Two concrete cases:
  - `pytest` on an empty `tests/` returns exit code 5 ("no tests collected").
    The Makefile `test` target and the `unit-tests`/`data-tests` CI jobs
    treat *only* exit 5 as the "nothing here yet" case and pass through any
    other nonzero exit (a real failure, or a collection error) unmasked.
  - `mypy src` on a `src/` tree with zero `.py` files exits 2 ("There are no
    .py[i] files in directory 'src'") rather than passing trivially. The
    `typecheck` Makefile target and CI job check for at least one `.py` file
    under `src/` first, and only invoke mypy when there is something to
    check — otherwise a correct, working typechecker would make the build
    red for a reason that has nothing to do with type errors.
- **Work owned by a concurrent agent that may or may not exist yet**
  (`scripts/verify_sources.py`, owned by `source-scout`) is guarded
  explicitly rather than assumed. `make verify-sources` fails loudly with a
  clear message (not a Python traceback) when the script is absent — this is
  the one case in this ADR where absence is a *failure*, not a "phase not
  started" no-op, because Gate 1 requires the verify script to exist and
  exit 0, and `cicd-engineer` should not paper over that gate criterion not
  being met yet by pretending success. `verify-sources.yml`, separately,
  treats the same absence as a reason to skip the job cleanly (green,
  explicit notice, no issue filed) rather than propagate that failure into a
  scheduled workflow that would otherwise file a spurious GitHub issue every
  week the script hasn't landed.
- **`web/` being empty** is handled the same way as the mypy case: `web.yml`
  checks for `web/package.json` before running any Node tooling, and reports
  plainly that there is nothing to lint/build/a11y-check yet rather than
  failing on a missing `package.json` or fabricating a pass.

### 8. Test files are not this agent's to create

`cicd-engineer` owns CI configuration and the Makefile, not test code — the
task's file-ownership list does not include anything under `tests/`. The
"prefer shipping a real trivial test" option for the `unit-tests` job in
`pr.yml` was therefore not taken; the zero-collected-tests tolerance
(exit code 5, see above) is the mechanism instead. The first real tests land
with the code they cover, starting Phase 2, owned by whichever agent writes
that code (`data-quality-auditor` per docs/build-plan.md §5.6 for
`tests/data/`).

## Consequences

- `uv.lock` must be committed and kept in sync; any pin bump goes through
  `uv lock` again, never a hand edit of a version string.
- CI jobs stay green through Phase 1–3 without asserting anything false —
  every "not implemented" message names the exact phase and section of
  docs/build-plan.md that will replace it, so the workflow files double as a
  literal, dated checklist of what's missing.
- `mypy`'s global `ignore_missing_imports` and the narrow `ruff` rule
  selection are both deliberately provisional and are flagged above for
  revisit once real code exists — this ADR should be amended (not silently
  overridden) when that happens.
- `verify-sources.yml` will only ever do real work once `source-scout` commits
  `scripts/verify_sources.py`; until then it is a scheduled no-op. That is
  expected to resolve within Phase 1, not left open-ended.

## Revisit if

- Real modules land in `src/` and the blanket `ignore_missing_imports`
  starts hiding genuine typing gaps in first-party code — switch to
  per-module `[[tool.mypy.overrides]]` for the specific third-party
  dependencies that lack stubs.
- The `ruff` `select` list needs to grow once there's actual code to lint
  against (e.g. `ANN` for annotation coverage, `S` for bandit-style security
  rules) — track that as a follow-up ADR or an amendment here, not a silent
  config change.
- `evals/harness.py` lands (Phase 4) — `pr.yml`'s `eval-fast-subset` job has
  a guard that fails loudly (not silently) if that file appears without the
  workflow being updated to actually run it; treat that failure as the
  trigger to replace the guard with a real invocation.
- `web/package.json` lands (Phase 4b) — same pattern: `web.yml`'s guard
  activates automatically the first time `frontend-engineer` commits a
  `package.json` with `lint`, `build`, and `test:a11y` scripts. If those
  script names turn out not to match what `frontend-engineer` actually
  ships, that's a `web.yml` update, not a reason to rename this ADR's
  assumption after the fact — fix the workflow.
