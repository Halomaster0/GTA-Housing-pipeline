# GTA Housing Pipeline

Four local governments in the Toronto area each publish their own records of new buildings and housing projects, in four different formats and with four different sets of definitions. This project collects that public data, reconciles it into one consistent set of tables, and lets someone ask plain-English questions about it and get answers tied back to the underlying records — with the entire build process, including its gaps, kept visible in this repository.

## Status

**Phase 1 of 5 — foundations and source verification. In active development.**

Nothing beyond the directory skeleton, this document, and repository scaffolding exists yet: no ingestion has run, no warehouse has been built, no AI layer exists, no dashboard is published, no web app is deployed, and no evaluation has been scored. Sections below are marked **(not yet built)** where that applies — take that marker literally, not as modesty. The full phase plan, gate criteria, and agent responsibilities behind this build live in [`docs/build-plan.md`](docs/build-plan.md).

## Live links

The intended public surface is a single Next.js application, with every artifact reachable from one link. **None of it is deployed yet.** No link below is live; this table exists so the intended shape is legible before the substance is, and so nobody has to guess at a URL that currently 404s.

| Route | Purpose | Status |
|---|---|---|
| `/` | System overview and live pipeline status | not yet deployed |
| `/ask` | Natural-language query console — answer, retrieved rows, executed SQL, trace | not yet deployed |
| `/dashboard` | Embedded Power BI report | not yet deployed |
| `/evals` | Live scorecard rendered from committed evaluation results | not yet deployed |
| `/architecture` | Architecture write-up | not yet deployed |

The one artifact that is live today is this repository.

## Architecture (target state — not yet built)

Nothing below this heading is running. This is the design the project is building toward, reproduced from the build plan so a reader does not have to open a second document to see the target shape.

```
┌─ SOURCES ────────────────────────────────────────────────────────────┐
│  Toronto CKAN REST API   │  Peel / Mississauga / Brampton ArcGIS Hub │
│  StatCan (CSV + SDMX)    │  (optional) CMHC housing starts           │
└────────────┬─────────────────────────────────────────────────────────┘
             │  extract (Python, idempotent, checkpointed)
             ▼
┌─ BRONZE ── raw landed files, immutable, partitioned by ingest_date ──┐
│            Parquet on local disk (dev) → OneLake (prod)              │
└────────────┬─────────────────────────────────────────────────────────┘
             │  DuckDB — typed, deduped, conformed
             ▼
┌─ SILVER ── cleaned entities: permits, applications, parcels,        ─┐
│            municipalities, census_tracts, dwelling_units             │
└────────────┬─────────────────────────────────────────────────────────┘
             │  hand-written gold SQL (no auto-generation)
             ▼
┌─ GOLD ──── star schema: fct_permits, fct_applications,              ─┐
│            dim_municipality, dim_date, dim_geography, dim_use_type   │
└──────┬──────────────────────────────────────┬────────────────────────┘
       │                                       │
       ▼                                       ▼
┌─ SERVING ─────────────────┐        ┌─ AI QUERY LAYER ────────────────┐
│  Microsoft Fabric         │        │  Planner agent                  │
│  → Power BI semantic model│◄───────┤  Retriever (embeddings/pgvector │
│  → published report       │        │    or LanceDB) + text-to-SQL    │
└───────────────────────────┘        │  Executor (read-only SQL)       │
                                     │  Critic (faithfulness check)    │
                                     └────────────┬────────────────────┘
                                                  ▼
                                     ┌─ EVAL HARNESS ──────────────────┐
                                     │  golden question set (~60 Qs)   │
                                     │  scored: correctness, faith-    │
                                     │  fulness, latency, cost, refusal│
                                     │  CI-gated, versioned results    │
                                     └────────────┬────────────────────┘
       │                                          │
       └──────────────────┬───────────────────────┘
                          ▼
┌─ PUBLIC WEB APP (URL decided at Gate 4b) ────────────────────────────┐
│  /            system overview + live pipeline status                 │
│  /ask         NL query console — answer, rows, SQL, trace            │
│  /dashboard   embedded Power BI report                               │
│  /evals       live scorecard rendered from evals/results/*.json      │
│  /architecture  the write-up, rendered                               │
└──────────────────────────────────────────────────────────────────────┘
```

**A note on the web app.** The Next.js application is deliberately a thin client over a documented FastAPI contract. It exists to make the rest of the system visible, not to be the point of the project. The engineering substance is the ingestion pipeline, the dimensional warehouse model, the multi-agent query orchestration graph, and the evaluation harness that scores it — all of which run and are testable independent of whether the frontend looks polished. Read this repository as a data and AI platform with a viewer attached to it, not as a Next.js application with a database behind it.

## What's genuinely hard about it

The hard part of this project is not calling four APIs. Toronto, Mississauga, Brampton, and Peel each publish their own definition of a "development application," a "unit," and a "status" — the same real-world event is categorized, timestamped, and counted differently depending on which portal it came from. Reconciling four incompatible schemas into one dimensional model is a modelling judgement, made row-type by row-type and documented with the reasoning attached, not a mechanical column-mapping exercise. Where the definitions genuinely cannot be reconciled without changing what a metric means, that gets written down as a decision record rather than quietly resolved by whichever mapping was convenient.

The second hard part is grounding. A language model asked a question about this data has to answer using the rows that were actually retrieved, not rows it recalls having seen somewhere or numbers it estimates as plausible. Asserting that an answer is grounded is easy; proving it is not. That proof has to come from a scored evaluation harness — a fixed set of questions with known-correct answers, checked mechanically for whether every number and every named entity in a response actually appears in the rows returned for that query — run in CI, with the scores from the losing runs published alongside the winning ones.

The third hard part is keeping the local build's fate independent of a cloud trial. The serving layer targets Microsoft Fabric and Power BI, and Fabric trials expire. DuckDB is the source of truth for development specifically so that if the Fabric trial lapses, the pipeline still runs, the tests still pass, and the data can still be queried and demonstrated locally without waiting on anyone's cloud subscription.

## Results

No numbers have been measured yet. Nothing has been ingested, transformed, retrieved, or evaluated. When a number does appear in this section, it will be accompanied by a link to the committed script and the committed output file that produced it — never a bare figure. Until then, this section stays exactly this short rather than gesturing at numbers that don't exist.

## How to run it

**Today, nothing in this repository produces a result yet.** What you can do right now is clone it and read the plan:

```bash
git clone https://github.com/Halomaster0/GTA-Housing-pipeline.git
cd GTA-Housing-pipeline
```

The intended developer workflow, once Phase 1 scaffolding is complete (tooling, dependencies, and CI are being built concurrently — see [`CONTRIBUTING.md`](CONTRIBUTING.md)), is a `Makefile`-driven setup:

```bash
make setup            # install pinned dependencies
make verify-sources   # confirm every data source is live before anything is built on it
make test             # run the test suite
make lint             # static checks
make typecheck        # type checks
make all              # the full local pipeline, start to finish
```

None of these targets should be assumed to exist or to succeed until a specific commit's CI run demonstrates it — check the workflow status on the commit in question rather than taking this section's word for it. This section will be rewritten with concrete, verified instructions as each piece lands, and the `oss-maintainer` role runs a "cold clone drill" — a fresh clone, followed literally from the README, timed — at every phase gate specifically to catch instructions that only work because of context that isn't written down.

## What it doesn't do

- **Not a real-estate price prediction model.** It does not forecast prices, and it makes no forecasting claims of any kind.
- **Not a startup.** There is no auth system, no billing, and no multi-tenancy. It is a single public read-only analytics artifact.
- **Not a scraper.** It ingests only from official municipal APIs and open-data endpoints — no scraping of pages that aren't meant to be machine-read.
- **Not a Kaggle notebook.** If a piece of work doesn't run on a schedule, unattended, it is not considered done, regardless of whether it produced a nice result once.

## Data sources and licences (not yet verified)

The target source families are:

- **Toronto** — CKAN REST API (open data portal)
- **Peel, Mississauga, and Brampton** — ArcGIS Hub REST endpoints
- **Statistics Canada** — CSV and SDMX data
- **CMHC housing starts** — optional, if licensing and access permit it

None of these has been confirmed live, licensed for public reuse, or profiled for the fields this project needs — that verification is the explicit job of Phase 1 and is tracked in [`docs/sources/`](docs/sources/) (currently empty; each source gets its own file once verified against a live call, not a search result) and enforced going forward by a committed `scripts/verify_sources.py` liveness check. No licence claim is made here until a source has been verified and its exact licence name recorded. Until then, treat every source in this list as unconfirmed.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for local setup, commit conventions, and the PR process; [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) for community standards; and [`SECURITY.md`](SECURITY.md) to report a vulnerability or a data-handling concern. This project is MIT licensed — see [`LICENSE`](LICENSE).
