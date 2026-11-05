# GTA Housing Pipeline

Four local governments in the Toronto area each publish their own records of new buildings and housing projects, in different formats and with different definitions. This project collects that public data, reconciles it into one set of DuckDB tables, and lets someone ask plain-English questions about it and get answers tied back to the underlying rows. The build process, including its gaps, is kept in this repository.

## Status

**Built and working locally:**

- **Ingestion and warehouse (Phases 1-2).** 20 ingest specs in `config/ingest.yml` pull from the Toronto open-data portal (CKAN), the Peel, Mississauga and Brampton ArcGIS endpoints, and Statistics Canada, into bronze files. DuckDB silver and gold layers are built from hand-written SQL in `models/`. Gates 1 and 2 are recorded as PASS in `docs/gates/`.
- **Power BI report (Phase 3).** A Power BI Project (`powerbi/gta-housing.pbip`) with five pages, plus a September PDF export. See [Power BI report](#power-bi-report).
- **AI query layer (Phase 4).** A planner, executor and critic over the gold warehouse, a 60-question golden set, and an eval harness that scores correctness, faithfulness and refusals. See [Results](#results).
- **Web app (Phase 4b).** A Next.js app in `web/` with the routes `/`, `/ask`, `/dashboard`, `/evals`, `/data-quality` and `/architecture`.

**Next steps:**

- **`/ask` is live** at [gta-housing-pipeline.vercel.app/ask](https://gta-housing-pipeline.vercel.app/ask). The next step is app-level spend tracking. Today the $0.50 cap is a limit on the OpenRouter key.
- **Publication (Phase 5):** the Lighthouse pass and the remaining human steps are tracked in [`OUTSTANDING.md`](OUTSTANDING.md).
- **Toronto net-unit counts** are held back from published figures until the audit in [`docs/data-exceptions.yml`](docs/data-exceptions.yml) is done. Published figures stay on the September build until October Toronto data is validated ([`docs/data-vintage-decision-2026-10-31.md`](docs/data-vintage-decision-2026-10-31.md)).
- **Fabric serving** is deferred ([ADR-0008](docs/decisions/0008-deferred-fabric-serving.md), [ADR-0010](docs/decisions/0010-pro-workspace-no-lakehouse.md)). Serving today is Power BI Desktop with a Pro workspace, and DuckDB is the source of truth.

## What is hard about it

Calling four APIs is not the hard part. Toronto, Mississauga, Brampton and Peel each define "development application", "unit" and "status" differently, so the same event is categorised and counted differently depending on the portal. Reconciling them into one dimensional model is a modelling judgement, made row type by row type and written up in [`docs/decisions/`](docs/decisions/) where the definitions cannot be reconciled without changing what a metric means.

Grounding is the second hard part. An answer has to rest on the rows that were actually retrieved. The claim is tested by a fixed set of 60 questions with known answers, checked mechanically for whether each number in a response appears in the rows returned. Committed runs live under `evals/results/`, weaker ones included.

The third is keeping the build independent of any cloud trial. DuckDB is the source of truth, so the pipeline, the tests and the queries still run locally if a Fabric trial lapses.

## How the pipeline fits together

```
Toronto CKAN, Peel / Mississauga / Brampton ArcGIS, Statistics Canada
  |  src/ingest (config/ingest.yml, 20 specs)
  v
data/bronze/{source}/ingest_date=YYYY-MM-DD/      raw files, one partition per run
  |  src/transform runs models/silver/*.sql       (10 files)
  v
silver tables in data/warehouse.duckdb
  |  src/transform runs models/gold/*.sql         (5 dimensions, 2 facts)
  v
gold star schema in data/warehouse.duckdb
  |-- scripts/export_gold_parquet.py -> gold CSV / Parquet -> Power BI report
  |-- src/ai: planner -> executor -> critic, served by src/ai/api.py on Vercel -> web/ /ask
  '-- evals/harness.py (60 golden questions) -> evals/results/*.json -> web/ /evals
```

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** manages the pinned Python 3.11 and every dependency. There is no `pip` fallback, because the project has no build backend.
- **Node.js 22** for `web/` (the version CI uses).
- **Internet access** for `make ingest` and `make verify-sources`.
- **An OpenRouter API key** for `/ask` and the eval harness. Nothing else needs a key.
- **Power BI Desktop** (Windows) to open the report.
- **`make` is optional.** The Makefile wraps the commands below, and `make help` lists the targets. `make` is not installed by default on Windows, so run the commands directly there.

## Setup

```bash
git clone https://github.com/Halomaster0/GTA-Housing-pipeline.git
cd GTA-Housing-pipeline
uv sync --extra dev --extra api     # pinned pipeline, dev tools and the FastAPI service
```

`make setup` runs `uv sync --extra dev`, which is enough for the pipeline and tests without the API.

If you plan to commit, install the git hooks once per clone with `uv run pre-commit install`. They run ruff, gitleaks and commitlint.

## Build the data

`data/` is git-ignored and nothing in it is committed. Build it from source:

```bash
uv run python -m src.ingest --all                           # make ingest: fetch every spec into data/bronze/
uv run python -m src.transform --all --report               # make transform: build silver and gold in data/warehouse.duckdb
uv run python scripts/export_gold_parquet.py --format csv   # make export-csv: gold CSVs in data/gold-csv/
uv run python scripts/export_gold_parquet.py                # make export-gold: gold Parquet in data/gold-parquet/
```

Two things to know before you commit anything:

- `make transform` deletes and rebuilds `data/warehouse.duckdb`, and it rewrites `docs/data-quality-report.md`, which is tracked. Review that diff before committing.
- `make reconcile` (`uv run python scripts/reconcile_measures.py`) rewrites `docs/measure-reconciliation.json`, which is also tracked.

To check that every source is still live, run `uv run python scripts/verify_sources.py` (`make verify-sources`). It needs internet access.

## Checks

```bash
uv run pytest                 # make test (data tests skip if no built warehouse)
uv run ruff check .           # make lint
uv run ruff format --check .  # the format check CI runs
uv run mypy src               # make typecheck
```

## Eval harness

```bash
uv run python evals/harness.py --limit 10   # quick smoke run
uv run python evals/harness.py              # make eval: all 60 questions
```

The harness needs a warehouse at `DUCKDB_PATH` (see [Environment](#environment)) and `OPENROUTER_API_KEY`. A full run makes LLM calls for every question and took 17 to 23 minutes in the committed runs.

Each run writes `evals/results/{date}-{git sha}.json`, **including a failed run**. Without a warehouse or key, the harness writes a 0% result and exits 1. Delete that file before committing.

## Web app

```bash
cd web
npm ci
npm run dev           # development server, http://localhost:3000
npm run build         # production build; static pages go to web/out/
npm run lint
npm run test:a11y     # static accessibility checks on web/out/ (run after build)
```

`npm run test:a11y` passes on all seven pages.

`/ask` needs the FastAPI service. The site reads `NEXT_PUBLIC_API_URL` at build time. If it is unset, `/ask` shows a "not connected" message and sends no request.

## The query API (`/ask` backend)

```bash
uv run --extra api python -m src.ai.server   # FastAPI on http://localhost:8000; GET /health, POST /ask
```

This needs a warehouse at `DUCKDB_PATH` and `OPENROUTER_API_KEY`.

In production the same code runs on Vercel as the `gta-housing-api` project. `app.py` exposes `src/ai/api.py`, and `.vercelignore` ships the September warehouse. The production settings are `OPENROUTER_API_KEY` (secret), `ALLOWED_ORIGINS` (the site's origin) and `TRACES_DIR=/tmp/traces`. The project's framework is set to FastAPI in its settings, not in the repo.

## Environment

Copy `.env.example` to `.env` (git-ignored) and uncomment or fill in only what you need. Blank numeric values crash the config loader, so leave a line commented out rather than blank. The variables the code reads are:

| Variable | Default | Used for |
|---|---|---|
| `OPENROUTER_API_KEY` | none | LLM calls in the query layer and the eval harness |
| `DUCKDB_PATH` | `data/warehouse-sept.duckdb` | warehouse read by `/ask` and the eval harness |
| `NEXT_PUBLIC_API_URL` | none | build-time address of the query API the site calls for `/ask` |
| `LLM_DAILY_SPEND_CEILING_USD` | `2.0` | daily spend ceiling for LLM calls |
| `API_RATE_LIMIT_PER_MINUTE` | `60` | per-IP rate limit on the API |
| `LOG_LEVEL` | `INFO` | structlog level |

## Data you need locally

| Path | Made by | Used by |
|---|---|---|
| `data/bronze/` | `make ingest` | `make transform` |
| `data/warehouse.duckdb` | `make transform` | exports, reconcile, data tests |
| `data/gold-csv/` | `make export-csv` | Power BI report (gold CSV import) |
| `data/gold-parquet/` | `make export-gold` | the serving contract ([ADR-0008](docs/decisions/0008-deferred-fabric-serving.md)) |
| `data/warehouse-sept.duckdb` | **no command in this repo** | default `DUCKDB_PATH` for `/ask` and the harness |
| `data/gold-sept-csv/` | **no command in this repo** | default `GoldCsvFolder` in the Power BI model |

The two September paths are local files that hold the 2026-09-10 build, which is what the published report shows (see [`docs/data-vintage-decision-2026-10-31.md`](docs/data-vintage-decision-2026-10-31.md)). To run `/ask` or the harness against what `make transform` builds, set `DUCKDB_PATH=data/warehouse.duckdb`. The October warehouse has different counts from the September build, so answers will differ from the committed September-era runs.

## Power BI report

- `powerbi/gta-housing.pbip` opens in Power BI Desktop. It has five pages: GTA overview, municipal comparison, pipeline velocity, geography, and data quality.
- The semantic model is generated TMDL in `powerbi/gta-housing.SemanticModel/` by `scripts/generate_pbip.py`. The report pages are generated by `scripts/generate_pbir_report.py`. Check both match the generators with `uv run python scripts/generate_pbip.py --verify-output` and `uv run python scripts/generate_pbir_report.py --verify`. See [`docs/powerbi-manual.md`](docs/powerbi-manual.md) §14.
- On first open, set the `GoldCsvFolder` parameter (Transform data, then Manage parameters) to an absolute path to the folder `make export-csv` wrote, normally `data/gold-csv`. The default points at `data\gold-sept-csv`, which no command creates.
- `powerbi/Exports/gta-housing.pdf` is a PDF export of the report from the September build.
- **The copy in the Power BI service is not refreshed from this repository.** Treat it as stale. The local `.pbip` and the PDF are the reference.

## AWS analytics layer

An optional path that copies the September gold tables to S3 as Parquet, describes them in a Glue catalog, and queries them with Athena. A least-privilege reader role runs the queries, and a parity test checks the answers against DuckDB. It sits beside the pipeline and changes nothing in it. No AWS resource is reachable from the public site or `/ask`.

```
DuckDB (data/warehouse-sept.duckdb)
  └─ scripts/export_gold_parquet.py ──> data/gold-parquet/*.parquet
       ├─ scripts/aws/gen_glue_schema.py ──> infra/aws/tables.auto.tfvars.json
       └─ scripts/aws/upload_gold.py ──> S3 curated bucket  gold/<table>/
                                           │
Glue database (7 external tables) ─────────┤
                                           ▼
Athena workgroup (enforced, 100 MiB scan cutoff) ──> S3 results bucket
                                           ▲
gta-housing-athena-reader (assumed by the test) ── tests/integration/test_athena_parity.py
```

**Commands** (run from the repo root, with the `gta-housing` profile signed in):

```bash
uv run python scripts/export_gold_parquet.py --warehouse data/warehouse-sept.duckdb --out-dir data/gold-parquet
uv run python scripts/aws/gen_glue_schema.py                 # regenerate the table definitions
make aws-plan                                                # Terraform plan; creates nothing
make aws-verify                                              # upload, then the parity test
```

Use the export script directly, as shown above. `make export-gold` reads the default October warehouse, and it takes no arguments.

`make aws-verify` needs these set in the shell: `AWS_PROFILE`, `ATHENA_WORKGROUP`, `ATHENA_READER_ROLE_ARN`, `ATHENA_CURATED_BUCKET` (the Terraform outputs give the last three). `make aws-destroy` prints the teardown command and does not run it.

**What it proves:** the September gold tables read through Athena, as a read-only reader role, return the same row counts and the same grouped figures as DuckDB, and the published anchors (827,919 permit records, 21,658 applications, 647,589 permits issued) match the reconciliation file. It also proves the reader role is denied writes and Glue table changes.

**What it does not prove:** Athena performance, behaviour at any real scale, a production data lake, or a current Power BI or `/ask` integration. The data is a September snapshot, not a live copy.

**Status:** deployed to a personal AWS account for verification (us-east-2, applied 2026-11-05), not torn down. The parity test passes: 13 of 13 tests, including the negative tests, against the September gold tables. The evidence is in [`docs/aws-parity-report.md`](docs/aws-parity-report.md). The decision and its limits are in [ADR-0011](docs/decisions/0011-aws-analytics-layer.md).

## Results

The latest committed eval run is [`evals/results/2026-11-02-2571861.json`](evals/results/2026-11-02-2571861.json) (git `2571861`, faithfulness metric v3): 60 questions, **90.0% correctness**, 100% faithfulness, 100% refusal accuracy.

Only compare runs with the same `faithfulness_metric_version`. The earlier runs in `evals/results/` have no version field and used an unversioned metric. `2026-11-02-2571861-metric2.json` is the same commit scored under metric v2.

## Repository layout

- `config/` ingest specs and the source registry
- `src/ingest`, `src/transform`, `src/common`, `src/ai` the pipeline and query layer
- `models/silver`, `models/gold` hand-written SQL, with a grain header on every file
- `scripts/` exports, source and measure checks, Power BI generators
- `evals/` golden questions, the harness and committed results
- `tests/` unit and data tests
- `web/` the Next.js app
- `powerbi/` the Power BI project and PDF export
- `docs/` the build plan, decisions (ADRs), gate records, data dictionary, source notes and handovers

Start with [`docs/build-plan.md`](docs/build-plan.md) for the plan and phase gates, and [`OUTSTANDING.md`](OUTSTANDING.md) for what remains.

## What it doesn't do

- **It is not a price model.** It does not forecast prices or make forecasting claims.
- **It is not a startup.** There is no auth, billing or multi-tenancy. It is a single public read-only analytics artifact.
- **It is not a scraper.** It reads only official municipal APIs and open-data endpoints.

## Contributing and licence

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for local setup, commit conventions and the PR process, [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md), and [`SECURITY.md`](SECURITY.md) to report a vulnerability or a data-handling concern. This project is MIT licensed; see [`LICENSE`](LICENSE).
