# Contributing to GTA Housing Pipeline

Thanks for looking at this. The project is public from its first commit and built in the open — see [`docs/build-plan.md`](docs/build-plan.md) for the full plan, the phase gates, and the reasoning behind the roles referenced below. This document covers the mechanics of contributing.

## Project status

This is early — Phase 1 of a 5-phase build (see the [README](README.md#status) for the current honest state). Expect gaps, stubs, and `not yet built` markers. That's not a reason to hold back a contribution; it's context for what "done" means at this point.

## Local setup

Setup is driven by the `Makefile` (owned and being built concurrently with this document — check its current contents rather than assuming every target below already works):

```bash
make setup            # install pinned dependencies
make verify-sources   # confirm every data source this project depends on is actually live
make test             # run the test suite
make lint             # static analysis / style checks
make typecheck        # type checks
make all              # the full local pipeline: setup, ingest, transform, test, eval
```

Run `make verify-sources` before you build anything that depends on a data source. If it fails, the source is not something to build against yet — file an issue with the `data-source` label instead (template below).

Copy `.env.example` to `.env` for any local configuration. Never commit a real `.env` file, an API key, or a connection string — see the secrets section below.

## Conventional Commits

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/), enforced by commitlint in pre-commit. Format:

```
<type>(<scope>): <short summary>

<optional body>
```

**Allowed types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.

**Scope convention** — use the layer the change touches:

| Scope | Covers |
|---|---|
| `ingest` | Source connectors, extraction, bronze landing |
| `transform` | Silver/gold SQL, DuckDB models, the star schema |
| `ai` | Retrieval, planner/executor/critic, the query graph |
| `api` | The FastAPI service |
| `web` | The Next.js public app |
| `docs` | README, architecture doc, ADRs, any documentation |
| `ci` | GitHub Actions, Makefile, tooling |
| `evals` | Golden question set, harness, eval results |

Examples: `feat(ingest): add Toronto CKAN connector with checkpointing`, `fix(transform): correct grain of fct_permits after Brampton status change`, `docs(readme): mark eval scores as measured`.

Commits with messages like `wip`, `fix stuff`, or `asdf` will be rejected by commitlint and are not acceptable even before enforcement lands — the git history here is public and permanent, and a hiring manager scrolling it is a real audience.

## Branch naming

`type/short-description`, matching the commit type where it applies — e.g. `feat/toronto-ckan-connector`, `fix/brampton-status-grain`, `docs/architecture-writeup`.

## Pull request process

1. Open an issue first for anything non-trivial, so the approach can be discussed before code is written.
2. Keep PRs scoped to one concern. A PR that touches ingestion and the web app at once is two PRs.
3. Fill out the PR template completely, including the evidence section — pasted command output, not a description of what you expect it to do. "An agent's assertion is not evidence" is the standing rule here, and it applies to human contributors too.
4. A reviewer will check:
   - The relevant Director checklist in the PR template (data engineering, platform, AI, analytics, or product/frontend — whichever section of the system the PR touches)
   - That any new number in a doc or UI traces to a committed script and a committed output file (see Data truth, below)
   - That the secrets checklist is genuinely checked, not just ticked
   - That tests pass and, where the PR touches data, that data-quality checks pass or every exception is explained in writing
5. Squash or rebase before merge to keep history readable; no merge commits with generic messages.

## Secrets: the absolute rule

No secret — API key, token, connection string, credential of any kind — is ever committed. Not briefly, not in a commit that gets reverted, not in a `.env` that "was only local for a minute." Git history is public and permanent; a rotated key still sits there for anyone to find.

If a secret does land in the repository:

1. **Rotate it immediately** — treat it as compromised the instant it was committed, regardless of whether it was ever pushed.
2. **Rewrite git history** to remove it, in the same session, before the next push.
3. Escalate to the project owner immediately. See [`SECURITY.md`](SECURITY.md) for the full procedure.

Rotation without history rewrite is not sufficient, and history rewrite without rotation is not sufficient. Both, same session.

## Data truth

No number lands in a README, a doc, a dashboard, or a demo without a committed script that produced it and a committed output file it can be traced back to. "Improved X by Y%" requires a committed before-measurement, not a claim. If a metric can't currently be produced from a real run, the correct thing to write is that it hasn't been measured yet — not a placeholder, not an estimate, not a plausible-looking number.

This applies to contributions from anyone, including project agents. If you see a number in this repository that doesn't trace to a script and an output file, that's a bug — file it.

## Adding a new data source

1. **Verify it live first.** Fetch the canonical portal page or API endpoint directly with a real HTTP call. Do not trust a search result, an aggregator listing, or a cached description — those misreport availability. A source is not confirmed until a live call returns rows.
2. Write `docs/sources/{source}.md` covering: portal and canonical URL, API type, auth requirements, licence (the exact name, and confirmation it permits public portfolio use), update cadence, a real row count from a live call with the date, the fields available and their types, which fields this project needs and whether they exist, known gaps, rate limits and pagination behaviour, and the exact request used to verify it.
3. Add the source to `scripts/verify_sources.py` so its liveness is checked automatically going forward (this runs weekly in CI).
4. If the source is dead, licence-ambiguous, or missing a field the star schema depends on, that's not something to work around quietly — open an issue and flag it clearly.

## Good first issues

Issues labelled `good first issue` are scoped for a first contribution without needing the full context of the build plan. Start there if you're new to the project.

## Questions

Open an issue using the "Question" template rather than emailing — keeping the discussion in the repo keeps the record public and searchable for the next person with the same question.
