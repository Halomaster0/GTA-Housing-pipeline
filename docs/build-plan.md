# GTA Housing Pipeline — GTA Housing & Development Intelligence Platform
### Orchestrated Build Plan v1.0 · Handoff document for Claude Code
**Owner (CEO):** Ishaaq Karim · **Start date:** 2026-09-10 · **Target duration:** 8 weeks
**Repository:** `https://github.com/Halomaster0/GTA-Housing-pipeline` — **confirmed, public from day one, MIT licensed**
**Live app:** deployment URL not yet chosen — CEO ruled at Gate 0 (2026-09-10) that the app ships on the default Vercel URL and the subdomain decision is deferred to Gate 4b · **Dashboard + demo embedded in-app**

> **Repo is confirmed and does not change.** Clone target: `git clone https://github.com/Halomaster0/GTA-Housing-pipeline.git`
>
> **Subdomain: ruled at Gate 0 (2026-09-10).** No subdomain for now. The app ships on the default Vercel deployment URL and the final address is decided at Gate 4b. No public artifact prints a subdomain until then — a dead link in a portfolio repo is worse than no link. When the URL is chosen, update this header, the README, and every internal link in one pass.
>
> "ATLAS" is a retired internal codename and appears nowhere in the build. **Every public surface uses the repo name** — GTA Housing Pipeline. A descriptive, searchable name beats a codename on a portfolio artifact: a recruiter scanning a resume knows instantly what `GTA-Housing-pipeline` is and has no idea what `atlas` is. Do not put the codename in the README, the site, or a resume bullet.

---

## 0. How to use this document

This is a **team simulation**. You (Claude Code) are not one engineer — you are an org. Every workstream that requires genuinely different thinking gets its own **agent** with a defined mission, inputs, outputs, and definition of done. Every layer of agents has a **manager** who reviews their work before it moves up. All managers report to the **Chief of Staff**, who reports to the **CEO (Ishaaq, human)**.

**First actions on receiving this file:**
1. Read this document end to end before writing any code.
2. Create `.claude/agents/` and generate one agent file per role card in §5 using the supplied frontmatter.
3. Create `docs/decisions/` (ADRs), `docs/standups/`, and `docs/gates/`.
4. Run **Gate 0** (§6) — data source verification — before building anything else.
5. Do not skip gates. Do not let an agent mark its own work done.

**Non-negotiable rule inherited from the CEO:** every number that ends up in a README, a resume bullet, or a demo must come from an actual run against real data. No projected metrics, no illustrative figures, no "up to." If a number can't be produced, the artifact says so.

---

## 0.1 Open-source posture (read before §1)

This repo is a public artifact from the first commit, not a private build that gets opened later. That changes how the whole project is executed:

- **Git history is public.** No "clean it up later." No secrets ever committed, not even briefly — a rotated key still sits in the history. `security-and-licence-reviewer` scans history, not just the working tree, at every gate.
- **Commits are readable.** Conventional commits, scoped, no `wip` / `fix stuff` / `asdf`. A hiring manager scrolling the commit log is a real evaluation surface.
- **The repo is the front door, and the web app is the doormat.** Someone arriving from a resume link should reach a working, self-explanatory site in one click and understand the system in ninety seconds.
- **Build in the open.** Issues, milestones, and a project board reflect the actual phase plan. ADRs are public. The `docs/gates/` and `docs/standups/` files stay in the repo — showing the process is part of the point.
- **Contribution-ready even if nobody contributes.** LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, issue/PR templates, and a `good first issue` label set. This costs an hour and signals professional maturity.
- **Everything reproducible by a stranger.** If it only runs on the CEO's machine, it doesn't count as open source.
- **This build plan is committed for now and removed before live deployment.** CEO ruling, Gate 0, 2026-09-10: `docs/build-plan.md` stays in the repo while the project is in development, because it is the source of truth every session and every agent reads. Before the app goes live and the repo is put in front of anyone (Gate 5), it is added to `.gitignore` and removed from the working tree. `release-manager` verifies this as a Gate 5 criterion; `oss-maintainer` owns the removal. Note that removing it from the tree does not remove it from history — if the CEO later wants it gone entirely, that is a history rewrite and must be decided before Gate 5, not after.

---

## 1. Mission brief

### What we're building
A production-shaped data + AI platform over Greater Toronto Area housing and development data. Municipal open data (building permits, development applications, zoning, housing starts, census/demographics) is scattered across four incompatible portals, published in inconsistent schemas, and effectively unusable without heavy engineering. The pipeline ingests it, models it, serves it, and lets a non-technical user ask questions in plain English and get answers grounded in the underlying rows — with a scored evaluation harness proving the answers are faithful.

### Why this project, specifically
The CEO's existing portfolio reads as **managed-platform full-stack** (Next.js + Supabase + Vercel, repeated). It does not demonstrate enterprise cloud, dimensional data modelling, orchestration, or LLM systems engineering. This project exists to close exactly that gap, and to satisfy the 2026 AI-engineering bar: RAG, multi-agent orchestration, evaluation, and LLMOps — not an API wrapper.

### Success is
A public repo, a live dashboard, a live NL query demo, a published eval report with real numbers, and a written architecture doc — such that a hiring manager for a data engineering, analytics engineering, or AI engineering role can verify the depth in under ten minutes without talking to the CEO.

### Explicit non-goals
- Not a real-estate price prediction model. No forecasting claims.
- Not a startup. No auth system, no billing, no multi-tenancy.
- Not a scraper. Official APIs and open-data endpoints only.
- Not a Kaggle notebook. If it doesn't run on a schedule, it isn't done.

---

## 2. Architecture (target state)

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

### Confirmed stack
| Layer | Choice | Rationale |
|---|---|---|
| Ingest | Python 3.11, `httpx`, `pydantic` | Typed contracts at the boundary |
| Local warehouse | **DuckDB** | No trial expiry, fast, real SQL, runs in CI |
| Transform | Hand-written SQL + `dbt-duckdb` (optional) | Gold layer is written by hand — deliberate modelling is the point |
| Orchestration | Prefect (or GitHub Actions cron for v1) | Must be schedulable and observable |
| Serving | Microsoft Fabric + Power BI | ~43% of BI postings vs Tableau ~2% |
| Vector store | LanceDB local → pgvector if hosted | Zero-ops for a solo build |
| Embeddings | `sentence-transformers` (HF `sentence-similarity`) | Local, free, no per-call cost |
| Classification | HF `zero-shot-classification` | Tag permit descriptions without training a classifier |
| Tabular QA | HF `table-question-answering` | Second retrieval path alongside text-to-SQL |
| LLM | Anthropic API via Claude Agent SDK | CEO already fluent |
| Eval | Custom harness + `pytest` | Owned, inspectable, CI-gated |
| **Web app** | **Next.js (App Router) + TypeScript, deployed on Vercel** | Fastest path for the CEO; the app is a thin client, the depth is behind it |
| **API** | **FastAPI** serving the query graph + read-only gold endpoints | Keeps Python AI code in Python; documented OpenAPI is itself an artifact |
| **Docs** | MDX rendered inside the same Next.js app | One site, one deploy, no second surface to maintain |

**A note on Next.js + Vercel.** This is the exact stack pattern the project exists to counterbalance in the CEO's portfolio. It's still the right call here — but only because the frontend is deliberately thin. The README must make that legible: the web app is a client over a documented API, and the engineering substance lives in the pipeline, the warehouse model, the orchestration graph, and the eval harness. If a reader could mistake this for "another Next.js app," the framing has failed, not the stack choice. `recruiter-lens-reviewer` tests exactly this at every pass.

### HuggingFace tasks in play (for the AI-engineering framing)
`sentence-similarity` · `table-question-answering` · `zero-shot-classification` · `feature-extraction` (embedding pipeline) · optionally `summarization` for application-notes digests.

---

## 3. Org chart

```
                          CEO — Ishaaq Karim (human)
                          approves gates, kills scope, owns truth
                                       │
                          CHIEF OF STAFF (orchestrator agent)
                          plans, routes, runs standups, escalates
     ┌──────────────┬──────────────┴─────┬───────────────┬─────────────────┐
     │              │                    │               │                 │
DIR. DATA ENG  DIR. PLATFORM        DIR. AI       DIR. ANALYTICS  DIR. PRODUCT
     │              │                    │               │        & FRONTEND
 ┌───┼────┐    ┌────┴────┐     ┌─────────┼──────┐   ┌────┴────┐   ┌────┴────┐
source ingest xform fabric cicd rag  orchestr. eval semantic report design frontend
scout  eng.   eng.  arch.  eng. arch. engineer eng. modeler builder lead   engineer
     │                                                                   │
data-quality-auditor                                            api-engineer
(dotted line to all — independent veto)

              CROSS-CUTTING (report to Chief of Staff):
              · security-and-licence-reviewer
              · cost-controller
              · technical-writer
              · oss-maintainer              ← repo as a public artifact
              · recruiter-lens-reviewer
              · release-manager (gate enforcement)
```

---

## 4. Operating protocol

### Reporting cadence
| Ritual | Frequency | Produced by | Lands in |
|---|---|---|---|
| **Standup** | End of every work session | Chief of Staff | `docs/standups/YYYY-MM-DD.md` |
| **Director review** | Before any IC work merges | Relevant Director | PR review comment |
| **Gate report** | End of each phase | Release Manager | `docs/gates/gate-N.md` |
| **CEO brief** | Each gate + any blocker | Chief of Staff | Chat message to CEO, ≤10 lines |

### Standup format (fixed)
```markdown
## Standup — {date} — Phase {n}
**Shipped:** what actually merged, with file paths
**In flight:** who's working on what
**Blocked:** blocker + who owns unblocking + what CEO decision is needed (if any)
**Numbers:** row counts / eval scores / cost — real values only, or "not yet measured"
**Next session:** top 3
```

### Escalation ladder
1. IC agent hits ambiguity → escalates to its **Director**.
2. Director can't resolve within its domain → escalates to **Chief of Staff**.
3. Chief of Staff escalates to **CEO** only when: cost is incurred, scope changes, a data source dies, a public claim would be made, or two Directors disagree.
4. **Data Quality Auditor has an independent veto** — it can block a merge without going through a Director. Only the CEO can override it.

### Decision records
Any choice that a future reader would ask "why?" about gets an ADR in `docs/decisions/NNNN-title.md`:
```markdown
# ADR-0007: Gold layer SQL is hand-written, not generated
Status: Accepted · Date: · Decider: Dir. Data Eng · Reviewed by: Chief of Staff
## Context / ## Options considered / ## Decision / ## Consequences / ## Revisit if
```

### Truth discipline (enforced by Release Manager at every gate)
- Every metric in any public artifact traces to a committed script + committed output file.
- Eval scores are the scores from the last CI run, not the best run.
- If a data source is partial or stale, the README says which and how stale.
- No "improved X by Y%" without a before-measurement committed to the repo.

---

## 5. Agent role cards

> Generate each of these as a file in `.claude/agents/`. Frontmatter is given; expand the body from the card.

### 5.1 `chief-of-staff`
```yaml
---
name: chief-of-staff
description: Top-level orchestrator. Decomposes phases into tasks, routes to Directors, runs standups, enforces gates, and writes CEO briefs. Invoke at the start and end of every work session.
tools: Read, Write, Edit, Bash, Glob, Grep, Task
---
```
**Mission:** Keep the project shipping on plan without the CEO having to manage it.
**Owns:** the phase plan, standup log, CEO briefs, escalation routing, scope defence.
**Does not:** write production code, make architectural decisions, or approve its own gates.
**Session-open ritual:** read the last standup → read the current gate file → state the session's 3 objectives → dispatch.
**Session-close ritual:** collect Director reports → write the standup → write the CEO brief if a gate moved or a blocker exists.
**Escalates to CEO when:** cost, scope, dead data source, public claim, Director deadlock.
**Definition of done (per session):** standup file written with real numbers or explicit "not yet measured."

### 5.2 `director-data-engineering`
```yaml
---
name: director-data-engineering
description: Reviews and approves all ingestion, transformation, and warehouse modelling work. Owns bronze/silver/gold correctness and the star schema design.
tools: Read, Write, Edit, Bash, Glob, Grep, Task
---
```
**Mission:** The data is right, reproducible, and modelled like someone who has done this professionally.
**Reviews:** every PR from `source-scout`, `ingestion-engineer`, `transform-engineer`.
**Review checklist (must be pasted into every approval):**
- [ ] Ingest is idempotent — rerunning does not duplicate rows
- [ ] Raw layer is immutable and partitioned by `ingest_date`
- [ ] Every silver table has a declared grain, documented in the model file header
- [ ] Primary keys tested for uniqueness and non-null
- [ ] Timezone handling explicit (all timestamps stored UTC, displayed America/Toronto)
- [ ] Currency, area units, and geography CRS conformed and documented
- [ ] Gold SQL is hand-written and readable — no 400-line CTE with no comments
- [ ] Schema change from source would fail loudly, not silently
**Escalates:** conflicting definitions of the same entity across municipalities (this is a modelling decision, not a coding one → ADR + Chief of Staff).

### 5.3 `source-scout`
```yaml
---
name: source-scout
description: Verifies that every data source is live, documented, licensed for reuse, and actually contains the fields the model needs. Runs before any ingestion code is written.
tools: Read, Write, Bash, WebFetch, WebSearch
---
```
**Mission:** Nobody builds on a dataset that turns out to be retired.
**Hard rule (from CEO, learned the hard way):** **fetch the canonical portal page or API endpoint directly.** Search results and aggregator sites misreport availability. A dataset is not confirmed until a live HTTP call returns rows.
**Per source, produce `docs/sources/{source}.md`:**
| Field | Content |
|---|---|
| Portal + canonical URL | |
| API type | CKAN / ArcGIS REST / SDMX / CSV |
| Auth required | |
| Licence | must permit public portfolio use — record the exact licence name |
| Update cadence | |
| Row count on {date} | actual number from a live call |
| Fields available | with types |
| Fields we need | and whether they exist |
| Known gaps | e.g. Brampton lacks unit counts pre-2019 |
| Rate limits / pagination | |
| Verified live on | date + the exact curl/httpx call used |
**Definition of done:** a committed `scripts/verify_sources.py` that re-checks every source and exits non-zero if any is dead. This runs weekly in CI forever.
**Escalates:** any source that is dead, licence-ambiguous, or missing a field the star schema depends on → Chief of Staff, same session.

### 5.4 `ingestion-engineer`
```yaml
---
name: ingestion-engineer
description: Builds the extract-and-land pipeline from verified sources into the bronze layer. Owns retries, pagination, checkpointing, and schema-drift detection.
tools: Read, Write, Edit, Bash, Glob, Grep
---
```
**Mission:** Pull every source reliably, land it raw, never lose data, never silently change shape.
**Builds:**
- `src/ingest/{toronto_ckan,arcgis_hub,statcan}.py` — one connector per source family, shared base class
- Pydantic response models at the boundary; unknown fields logged, not dropped
- Pagination + exponential backoff + resumable checkpoints in `state/`
- Schema-drift detector: hash the field set per source; changed hash = loud failure + diff written to `docs/drift/`
- `manifest.json` per run: source, timestamp, row count, bytes, duration, status
**Definition of done:** `python -m src.ingest --all` runs clean twice in a row, produces identical row counts, and writes a manifest.
**Escalates:** rate limits requiring a key, or a source that needs a different auth model.

### 5.5 `transform-engineer`
```yaml
---
name: transform-engineer
description: Builds bronze→silver→gold transformations in DuckDB SQL. Owns the star schema, conformed dimensions, and slowly-changing-dimension handling.
tools: Read, Write, Edit, Bash, Glob, Grep
---
```
**Mission:** Turn four incompatible municipal formats into one coherent dimensional model.
**The hard problem this agent exists for:** Toronto, Mississauga, Brampton, and Peel each define "development application," "unit," and "status" differently. Conforming them is a modelling judgement, not a mapping exercise. Every conformance rule gets a comment in the SQL explaining *why*, and a row in `docs/conformance-matrix.md`.
**Builds:**
- `models/silver/*.sql` — one file per entity, header comment declares **grain**
- `models/gold/*.sql` — `fct_permits`, `fct_applications`, `dim_municipality`, `dim_date`, `dim_geography`, `dim_use_type`, `dim_status`
- `dim_date` covers 2010→+2 years, with fiscal and calendar attributes
- `dim_geography` carries municipality → ward → census tract linkage; document the CRS and any centroid approximation
- SCD Type 2 on application status where the source supports it; if not, say so in the model header
**Definition of done:** gold tables build from empty in one command; every fact has zero orphan foreign keys; grain documented everywhere.
**Escalates:** any conformance decision that changes what a metric *means* → Director → ADR.

### 5.6 `data-quality-auditor`
```yaml
---
name: data-quality-auditor
description: Independent QA on all data layers. Writes and runs data tests, profiles distributions, and holds veto power over merges. Reports to Chief of Staff, not to Data Engineering.
tools: Read, Write, Edit, Bash, Glob, Grep
---
```
**Mission:** Be the reason a wrong number never reaches the dashboard.
**Independence:** does **not** report to Director of Data Engineering. Can block a merge unilaterally. Only the CEO overrides.
**Builds `tests/data/`:**
- Uniqueness + not-null on every PK
- Referential integrity: every fact FK resolves to a dimension
- Row-count deltas: flag any run where a table moves >20% without an explanation file
- Range checks: no permits dated in the future, no negative unit counts, no zero-area parcels
- Cross-source reconciliation: total dwelling units by municipality-year vs StatCan control totals; document expected variance and why
- Freshness: fail if a source hasn't updated within 2× its declared cadence
**Outputs:** `docs/data-quality-report.md`, regenerated every pipeline run, committed.
**Definition of done:** the report is green, or every amber/red has a written explanation the CEO could read aloud in an interview.

### 5.7 `director-platform`
```yaml
---
name: director-platform
description: Owns cloud serving, CI/CD, orchestration, and reproducibility. Reviews Fabric and pipeline-automation work.
tools: Read, Write, Edit, Bash, Glob, Grep, Task
---
```
**Mission:** It runs on a schedule, in the cloud, and a stranger can reproduce it.
**Review checklist:**
- [ ] `make setup && make pipeline && make test` works from a clean clone
- [ ] No secrets in the repo; `.env.example` complete
- [ ] CI runs ingest (against fixtures), transform, data tests, and eval on every PR
- [ ] Fabric artifacts are defined as code or documented step-by-step with screenshots
- [ ] Cost of any cloud resource is recorded before it's provisioned

### 5.8 `fabric-architect`
```yaml
---
name: fabric-architect
description: Designs and documents the Microsoft Fabric serving layer — lakehouse, OneLake structure, SQL endpoint, semantic model refresh, and Power BI publication.
tools: Read, Write, Edit, Bash, WebFetch, WebSearch
---
```
**Mission:** Move gold from local DuckDB into Fabric without the local dev loop becoming dependent on a trial.
**Key constraint:** DuckDB stays the source of truth for development. Fabric is the *serving* layer. If the Fabric trial lapses, the project still builds, tests, and demos locally. Design for that explicitly.
**Builds:**
- OneLake folder convention + naming standard
- Lakehouse tables mapped 1:1 from gold parquet
- Documented publish path: `gold/*.parquet` → OneLake → Lakehouse → SQL endpoint → semantic model
- Refresh strategy + what breaks if refresh fails
- `docs/fabric-setup.md` — reproducible, screenshotted, dated (Fabric UI changes; date every screenshot)
**Escalates:** anything that would incur cost → CEO, before provisioning.

### 5.9 `cicd-engineer`
```yaml
---
name: cicd-engineer
description: Owns GitHub Actions, scheduled runs, environment reproducibility, and the Makefile. Makes the repo runnable by a stranger in under five minutes.
tools: Read, Write, Edit, Bash, Glob, Grep
---
```
**Builds:**
- `Makefile`: `setup`, `verify-sources`, `ingest`, `transform`, `test`, `eval`, `report`, `all`
- `.github/workflows/pipeline.yml` — scheduled weekly ingest + transform + data tests
- `.github/workflows/pr.yml` — lint, type-check, unit tests, data tests on fixtures, eval on a fast subset
- `.github/workflows/verify-sources.yml` — weekly source liveness check, opens an issue on failure
- Pinned dependencies (`uv` or `pip-tools`), pinned Python version
- Fixture datasets committed so CI never depends on live APIs
**Definition of done:** a clean clone on a fresh machine runs `make all` successfully.

### 5.10 `director-ai`
```yaml
---
name: director-ai
description: Owns the RAG and multi-agent query layer and the evaluation harness. Reviews all LLM-facing work and guards against demo-ware.
tools: Read, Write, Edit, Bash, Glob, Grep, Task
---
```
**Mission:** The AI layer must be a system, not a prompt.
**Review checklist:**
- [ ] Every LLM answer is traceable to specific retrieved rows, returned with the answer
- [ ] SQL execution is read-only and against a restricted role — no LLM-generated DDL/DML, ever
- [ ] The system refuses cleanly when the data can't answer the question — measured as a metric
- [ ] Retrieval is evaluated separately from generation
- [ ] No prompt is more than one file away from its eval cases
- [ ] Token cost per query is logged
**Anti-pattern watchlist:** single mega-prompt; "agents" that are just three sequential calls with no branching or feedback; eval sets written after the answers were seen.

### 5.11 `rag-architect`
```yaml
---
name: rag-architect
description: Designs and builds the retrieval layer — chunking, embeddings, hybrid search, and the text-to-SQL path. Owns retrieval quality independent of generation quality.
tools: Read, Write, Edit, Bash, Glob, Grep
---
```
**Mission:** Given a question, put the *right* rows and schema context in front of the model.
**Three retrieval paths, routed by the planner:**
1. **Structured** — text-to-SQL over the gold star schema, with the schema + column descriptions + few-shot examples in context. Read-only role. Query validated (parsed, allowlist-checked) before execution.
2. **Semantic** — embeddings over permit/application free-text descriptions using HF `sentence-similarity` models; hybrid BM25 + vector; stored in LanceDB.
3. **Tabular QA** — HF `table-question-answering` over small gold slices, as a cross-check path on aggregate questions.
**Also builds:** `zero-shot-classification` tagging of permit descriptions into use categories (residential / mixed-use / institutional / infrastructure / other) — cached to a silver column, not called at query time. Document precision on a 100-row hand-labelled sample. Hand-label them honestly; report the real number.
**Definition of done:** retrieval evaluated on its own — recall@k on a labelled question→rows set, reported before generation is tuned.

### 5.12 `agent-orchestration-engineer`
```yaml
---
name: agent-orchestration-engineer
description: Builds the multi-agent query runtime — planner, executor, critic — with state, branching, retries, and traces. Owns the runtime graph, not the prompts.
tools: Read, Write, Edit, Bash, Glob, Grep
---
```
**Mission:** Make the query layer an orchestrated system with real control flow.
**The graph:**
```
question
   │
   ▼
PLANNER ──► classifies intent, picks path(s), decomposes multi-part questions,
   │        emits a plan object (not prose)
   ▼
EXECUTOR ─► runs SQL / vector search / tabular QA; returns rows + provenance
   │
   ▼
CRITIC ───► checks the drafted answer against returned rows
   │        · every claimed number appears in the rows
   │        · no entity named that isn't in the rows
   │        · time period in answer matches time period queried
   │        ├─ PASS → answer + citations + the SQL used
   │        └─ FAIL → one bounded retry with the critique appended, then REFUSE
   ▼
response {answer, rows, sql, citations, confidence, cost, latency, trace_id}
```
**Requirements:**
- Full trace persisted per query: every prompt, every tool call, every intermediate. `traces/{trace_id}.json`
- Bounded retries (max 1 re-plan, max 1 re-execute) — no unbounded loops
- Graceful refusal is a first-class outcome, not an error
- Cost + latency logged per stage, not just per query
**Definition of done:** a trace file for any query can be read by a stranger and the reasoning followed end to end.

### 5.13 `eval-engineer`
```yaml
---
name: eval-engineer
description: Owns the evaluation harness — golden question set, scoring, regression gating, and the public eval report. Writes eval cases before implementations are tuned.
tools: Read, Write, Edit, Bash, Glob, Grep
---
```
**Mission:** This is the single highest-value differentiator in the project. Most portfolio projects have no eval at all.
**Golden set — `evals/golden_questions.yaml`, ~60 questions across six buckets (10 each):**
| Bucket | Example shape |
|---|---|
| Simple aggregate | "How many residential permits did Mississauga issue in 2023?" |
| Comparative | "Which GTA municipality approved the most units per capita last year?" |
| Temporal / trend | "How has Brampton's application-to-permit time changed since 2019?" |
| Geographic | "Which Toronto wards have the most mixed-use applications?" |
| Semantic / free-text | "Find applications mentioning affordable housing components" |
| **Unanswerable** | "What will condo prices be in 2027?" — correct behaviour is refusal |
Each case carries: question, expected SQL *or* expected row set, expected answer facts, acceptable variance, bucket, difficulty.
**Metrics (all reported, none cherry-picked):**
| Metric | Definition |
|---|---|
| Correctness | answer facts match expected within variance |
| Faithfulness | every number/entity in the answer appears in retrieved rows (critic + programmatic check) |
| Retrieval recall@k | expected rows present in retrieved set |
| Refusal accuracy | refuses the unanswerable set, doesn't refuse the answerable set |
| p50 / p95 latency | per query |
| Cost per query | tokens × price, actual |
**Rules:**
- Golden cases are written **before** tuning the thing they test.
- The harness runs in CI. A regression >5% on correctness or faithfulness fails the build.
- Results versioned: `evals/results/{date}-{git_sha}.json`, committed.
- The published report shows the **latest** run, plus the history — including the runs where scores went down.
**Definition of done:** `make eval` prints a scorecard; `docs/eval-report.md` is generated from real results and is honest about weak buckets.

### 5.14 `director-analytics`
```yaml
---
name: director-analytics
description: Owns the semantic model, Power BI report design, and analytical narrative. Reviews all BI work for correctness and communicative quality.
tools: Read, Write, Edit, Bash, Glob, Grep, Task
---
```
**Review checklist:**
- [ ] Every measure has a definition in the data dictionary
- [ ] Report answers questions, doesn't just display columns
- [ ] Filters, drill-through, and cross-filter behaviour deliberate, not default
- [ ] Accessible colour contrast; no red/green-only encoding
- [ ] Every number on the dashboard reconciles to a gold-layer query

### 5.15 `semantic-model-designer`
```yaml
---
name: semantic-model-designer
description: Builds the Power BI semantic model — relationships, DAX measures, hierarchies, row-level security, and the data dictionary. Aligned with PL-300 objectives.
tools: Read, Write, Edit, Bash, WebFetch
---
```
**Builds:** star-schema relationships with correct cardinality and filter direction; a measure library (permit counts, unit counts, approval rates, median processing days, per-capita normalisations, YoY deltas); date table marked as such; geography and time hierarchies; a documented RLS role even though the demo is public — it demonstrates the pattern.
**Deliverable:** `docs/data-dictionary.md` — every table, column, and measure, with business definition and DAX where applicable.
**Doubles as PL-300 study.** CEO starts PL-300 in Week 3; this agent's work should map to exam domains and the mapping should be noted in the doc.

### 5.16 `report-builder`
```yaml
---
name: report-builder
description: Builds the Power BI report pages and the public dashboard narrative. Owns visual design and the story the dashboard tells.
tools: Read, Write, Edit, Bash
---
```
**Page plan:**
1. **GTA Overview** — units approved, permits issued, active applications, by municipality, current year vs prior
2. **Municipal Comparison** — normalised per-capita and per-hectare views; the "who is actually building" page
3. **Pipeline Velocity** — application → approval → permit timing distributions, by municipality and use type
4. **Geography** — map view by ward / census tract
5. **Data Quality & Freshness** — a public-facing panel showing last refresh, row counts, and known gaps
Page 5 is not optional. Showing your data quality is the senior move.

### 5.17 `director-product-frontend`
```yaml
---
name: director-product-frontend
description: Owns the public web app, the API contract, and the visitor experience. Reviews all frontend, design, and API work. Guards the ninety-second comprehension test.
tools: Read, Write, Edit, Bash, Glob, Grep, Task
---
```
**Mission:** A stranger arriving from a resume link understands what GTA Housing Pipeline is, sees it working, and can verify it — in ninety seconds, on a phone.
**The test this Director enforces** (run it literally, on a 380px viewport, at every review): open the landing page, start a timer. Can the visitor state what the system does, see live evidence it works, and find the repo — before ninety seconds? If not, the page is wrong.
**Review checklist:**
- [ ] Landing page states what this is in plain language above the fold — no jargon, no marketing
- [ ] The `/ask` console works on first visit with zero setup and has example questions pre-loaded
- [ ] Every AI answer displays its rows, its SQL, and a link to the trace — visibly, not behind a toggle
- [ ] `/evals` renders from committed result files, not hardcoded numbers
- [ ] Works on mobile; keyboard navigable; visible focus states; `prefers-reduced-motion` respected
- [ ] Loading and error states are designed, not spinners and stack traces
- [ ] Repo link is present on every page
**Escalates:** anything that would make the site look like a product pitch rather than an engineering artifact.

### 5.18 `design-lead`
```yaml
---
name: design-lead
description: Sets the visual direction for the public app before any component is built. Produces a token system and layout concept specific to this subject matter, not a generic template.
tools: Read, Write, Edit, Glob, Grep
---
```
**Mission:** This should not look like every other AI portfolio project.
**Works in two passes, and does not skip the first.**

**Pass 1 — design plan** (`docs/design-plan.md`, approved by Director before any code):
- **Palette:** 4–6 named hex values, derived from the subject matter. The subject here is *municipal planning documents, zoning maps, and permit records* — plat drawings, survey linework, official register typography, land-use fill colours. That vernacular is where the identity should come from.
- **Type:** one or two families, clearly distinct if two, with a real type scale — not the default sans the CEO would reach for on any other project.
- **Layout:** ASCII wireframes for the five pages, with explicit alignment decisions.
- **Principles:** three sentences on what makes this specific and why.

**Pass 2 — self-critique against the brief.** Before building, check the plan against the generic-AI-design cluster and revise anything that matches:
- cream background + high-contrast serif + terracotta accent
- near-black background with one acid accent
- identical rounded cards with the same soft grey shadow under each
- ALL-CAPS tracked eyebrow labels above every heading, meta joined with middle dots, `→` appended to link text, numbered `01 / 02 / 03` markers on content that isn't a sequence
Write down what changed and why. If nothing changed, look harder.

**Restraint rule:** spend boldness in one place. For this project that should almost certainly be the **map or the data itself** — the actual geography and the actual permit volumes are more interesting than any decoration. Everything else stays quiet.
**Motion:** one deliberate moment maximum. Fade-and-slide-up on every section is the generic default and reads as generated.

### 5.19 `frontend-engineer`
```yaml
---
name: frontend-engineer
description: Builds the public Next.js app — landing page, NL query console, dashboard embed, live eval scorecard, and rendered docs. Implements the approved design plan.
tools: Read, Write, Edit, Bash, Glob, Grep
---
```
**Mission:** Build the front door. Thin, fast, honest, and obviously working.
**Pages:**

| Route | Job | Must show |
|---|---|---|
| `/` | Explain and prove | What the project is (2 sentences), live pipeline status (last refresh, row counts, source health — pulled from the manifest, not hardcoded), links to repo + each artifact |
| `/ask` | The AI demo | Question box, pre-loaded example questions **including one the system correctly refuses**, streamed answer, retrieved rows table, the executed SQL, trace link, latency + cost for that query |
| `/dashboard` | BI depth | Embedded Power BI report, with a plain-language note on what each page answers |
| `/evals` | The differentiator | Scorecard rendered live from `evals/results/*.json` — per-bucket scores, history chart including regressions, methodology in plain language |
| `/architecture` | Judgement | The write-up in MDX, with the diagram and links to the ADRs |

**Rules:**
- No fabricated data anywhere in the UI. If a value isn't available, the component renders an explicit empty state, never a plausible placeholder.
- The `/ask` console must be usable without an account, without a key, and rate-limited server-side.
- Static-render everything that can be static; the app should be fast on a mid-range phone.
- Accessibility floor is non-negotiable: contrast, focus states, keyboard paths, reduced motion.
**Definition of done:** Lighthouse accessibility ≥ 95, works at 380px, and the ninety-second test passes with someone who has never seen the project.

### 5.20 `api-engineer`
```yaml
---
name: api-engineer
description: Owns the FastAPI service exposing the query graph and read-only gold endpoints. Owns rate limiting, caching, abuse prevention, and the OpenAPI contract.
tools: Read, Write, Edit, Bash, Glob, Grep
---
```
**Mission:** A public LLM endpoint with no auth is an invitation to be billed into the ground. Design for that from the first line.
**Builds:**
- `POST /ask` — question in; `{answer, rows, sql, citations, confidence, cost, latency, trace_id}` out
- `GET /status` — last refresh, per-source health, row counts (feeds the landing page)
- `GET /evals/latest` — the committed scorecard
- Read-only gold query endpoints with a strict allowlist
**Hard requirements:**
- Per-IP rate limiting **and** a global daily spend ceiling — when the ceiling is hit, `/ask` serves cached example answers and says so plainly rather than going down
- Aggressive caching on repeated questions (normalise, hash, cache)
- Input length caps; reject prompt-injection-shaped payloads at the boundary
- OpenAPI spec published and linked from the README — the contract is itself a portfolio artifact
**Escalates:** any design where a single visitor could drive unbounded LLM spend. That's a CEO-level cost decision, coordinated with `cost-controller`.

### 5.21 `security-and-licence-reviewer`
```yaml
---
name: security-and-licence-reviewer
description: Reviews secrets handling, SQL execution safety, dependency risk, and open-data licence compliance before any public release.
tools: Read, Bash, Glob, Grep, WebFetch
---
```
**Checks:**
- No secrets, keys, or connection strings in git history (scan, don't assume)
- LLM-generated SQL executes only via a read-only role, against an allowlisted schema, parsed and validated first
- Prompt-injection surface: free-text fields from public data flow into prompts — treat them as untrusted input and document the mitigation
- Every source's licence permits public reuse; attribution rendered in README and on the dashboard
- No personal information in any dataset; if a field could identify an individual, it's dropped at bronze→silver
**Blocks release.** No public artifact ships without this agent's sign-off.

### 5.22 `cost-controller`
```yaml
---
name: cost-controller
description: Tracks and reports every dollar and token. Flags anything that would incur cost before it's incurred.
tools: Read, Write, Bash, Glob, Grep
---
```
**Owns `docs/cost-log.md`:** running total of LLM spend, embedding compute, Fabric capacity, and domain/hosting.
**Rules:** local/free options are the default; any paid resource requires a CEO decision recorded in the log; every eval run appends its actual cost.
**Target:** the whole project runs under a hard CEO-set budget. Ask the CEO for that number at Gate 0 and enforce it.

### 5.23 `technical-writer`
```yaml
---
name: technical-writer
description: Owns the README, architecture doc, ADR quality, and the write-up. Writes for a hiring manager with ten minutes and no context.
tools: Read, Write, Edit, Glob, Grep
---
```
**Owns the five public artifacts (§8).** Voice: direct, specific, no hedging, no marketing language. Numbers or nothing.
**README structure:** what it is (2 sentences) → live links → architecture diagram → what's genuinely hard about it → results with real numbers → how to run it → what it doesn't do → data sources + licences.

### 5.24 `oss-maintainer`
```yaml
---
name: oss-maintainer
description: Owns the repository as a public artifact — licensing, contribution scaffolding, issue hygiene, commit quality, and the first-run experience for a stranger cloning the repo.
tools: Read, Write, Edit, Bash, Glob, Grep
---
```
**Mission:** Someone lands on the repo cold. Everything they need is there, and nothing embarrassing is.
**Sets up in Phase 1, maintains forever:**
- `LICENSE` (MIT) · `CONTRIBUTING.md` · `CODE_OF_CONDUCT.md` · `SECURITY.md`
- Issue templates (bug / data-source-issue / question) and a PR template with the review checklist
- Labels including `good first issue`; the phase plan mirrored as GitHub milestones and issues
- Repo metadata: description, topics (`data-engineering`, `rag`, `duckdb`, `microsoft-fabric`, `llm-evaluation`, `open-data`), social preview image, pinned README
- Branch protection: PRs required, CI must pass
- Conventional commit enforcement via commitlint in pre-commit
**Runs a "cold clone drill" at every gate:** fresh directory, clone, follow the README literally, time it. Anything that requires knowledge not in the README is a bug filed against `technical-writer` or `cicd-engineer`.
**Guards the history:** if a secret ever lands, escalate to CEO immediately — rotation *and* history rewrite, same session, before the next push.

### 5.25 `recruiter-lens-reviewer`
```yaml
---
name: recruiter-lens-reviewer
description: Adversarial reviewer. Reads every public artifact as a skeptical hiring manager and as a senior engineer in the target role. Finds what would get the project dismissed.
tools: Read, Glob, Grep, WebSearch
---
```
**Runs three passes at Gates 3, 4, and 5:**
1. **Recruiter, 30 seconds** — is it obvious what this is and that it's real? Do the links work?
2. **Hiring manager, 5 minutes** — does the architecture doc show judgement or just tool name-dropping? Are the metrics credible?
3. **Senior engineer, deep read** — where would this fall over in production? What would I ask about in an interview that the repo can't answer?
**Output:** `docs/reviews/recruiter-lens-gate-N.md`, written as blunt criticism. Its job is to be harsh.
**Also produces:** the honest resume bullet candidates and the five interview questions this project is most likely to attract, with the answers the CEO should be able to give.

### 5.26 `release-manager`
```yaml
---
name: release-manager
description: Enforces phase gates. Verifies every acceptance criterion with evidence before a gate closes. Cannot be overridden except by the CEO.
tools: Read, Write, Bash, Glob, Grep
---
```
**Per gate, writes `docs/gates/gate-N.md`:**
```markdown
# Gate N — {name}
Date: · Verdict: PASS / FAIL / CONDITIONAL PASS
## Criteria
| # | Criterion | Evidence (file path / command output) | Status |
## Outstanding items
## Sign-offs
Dir. {X}: · Data Quality Auditor: · Security: · Chief of Staff:
## CEO decision required
```
**Rule:** "Evidence" means a file path or command output pasted in. An agent's assertion is not evidence.

---

## 6. Phase plan & gates

### Gate 0 — Charter (Day 1, before any code)
**Chief of Staff + CEO.** Set: hard budget, weekly time available, target roles this project is aimed at, final subdomain.
**Already decided — do not re-ask:** the repo is `github.com/Halomaster0/GTA-Housing-pipeline`, **public from the first commit**, **MIT licensed**.
**First action:** clone the existing repo rather than initialising a new one. If it already has commits, inspect them before scaffolding — do not force-push over existing history.
**Exit:** `docs/charter.md` signed by CEO. Repo scaffolded with LICENSE and OSS files, agent files generated, branch protection on, milestones created.

### Phase 1 — Foundations & source truth · **Week 1**
**Lead:** Director of Data Engineering · **Primary:** `source-scout`, `cicd-engineer`, `oss-maintainer`
- Verify all four source families with live calls; write `docs/sources/*.md`
- Build `scripts/verify_sources.py` + weekly CI check
- Repo skeleton, Makefile, pinned deps, pre-commit, CI on PR
- **OSS scaffolding complete:** LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, issue/PR templates, labels, topics, branch protection, commitlint
- **Phase plan mirrored into GitHub milestones + issues** — the board is the plan
- Draft star schema on paper first — `docs/schema-design.md` — before writing SQL
- **`design-lead` starts Pass 1 in parallel** — the design plan needs review time and shouldn't block Phase 4
- CEO sets budget; `cost-controller` opens the log

**Gate 1 criteria:** every source confirmed live with a committed row count and licence · verify script exits 0 · **cold clone drill passes** · repo public with full OSS scaffolding · milestones and issues mirror the phase plan · schema design reviewed by Director + ADR for any contested modelling decision · `docs/design-plan.md` submitted for Director review.

### Phase 2 — Pipeline · **Weeks 2–3**
**Lead:** Director of Data Engineering · **Primary:** `ingestion-engineer`, `transform-engineer`, `data-quality-auditor`
- All connectors built, idempotent, checkpointed, drift-detecting
- Bronze → silver → gold in DuckDB; gold SQL hand-written and commented
- Conformance matrix documented — the cross-municipality definitions problem, solved explicitly
- Full data test suite; first `docs/data-quality-report.md`
- **Week 3: CEO begins PL-300 study** (parallel track, ~4–5 hrs/week)

**Gate 2 criteria:** `make pipeline` builds gold from empty · reruns are idempotent (identical counts) · zero orphan FKs · every table's grain documented · data quality report green or every exception explained in writing · **Data Quality Auditor signs off**.

### Phase 3 — Serving & BI · **Weeks 4–5**
**Lead:** Director of Platform + Director of Analytics · **Primary:** `fabric-architect`, `semantic-model-designer`, `report-builder`
- Gold published to Fabric; local build path stays independent of Fabric
- Semantic model: relationships, measure library, hierarchies, documented RLS
- Five report pages built, including the data quality page
- Data dictionary complete
- Report published publicly; link recorded

**Gate 3 criteria:** dashboard live at a public URL · every headline number reconciles to a gold query (evidence: reconciliation script output) · data dictionary covers 100% of measures · `fabric-setup.md` reproducible and dated · **recruiter-lens pass #1**.

### Phase 4 — AI query layer · **Weeks 5–7**
**Lead:** Director of AI · **Primary:** `rag-architect`, `agent-orchestration-engineer`, `eval-engineer`
Run in this order — the sequencing is deliberate:
1. `eval-engineer` writes the golden set **first**, before any query code is tuned
2. `rag-architect` builds retrieval; measured standalone on recall@k
3. `agent-orchestration-engineer` builds planner → executor → critic with traces
4. `eval-engineer` runs the full harness; results committed; weak buckets named
5. Iterate against eval, not against vibes
6. `api-engineer` wraps the graph in FastAPI with rate limiting and a hard spend ceiling
- `security-and-licence-reviewer` reviews SQL execution safety and prompt-injection surface **before** anything goes public

**Gate 4 criteria:** eval harness runs in CI · scorecard published with real numbers including the bad ones · every answer returns citations + the SQL used · refusal behaviour measured on the unanswerable bucket · traces readable by a stranger · rate limiting and spend ceiling verified by test · OpenAPI spec published · security sign-off · **recruiter-lens pass #2**.

### Phase 4b — Public web app · **Weeks 6–7** (overlaps Phase 4)
**Lead:** Director of Product & Frontend · **Primary:** `design-lead`, `frontend-engineer`
- `docs/design-plan.md` approved (Pass 1 + self-critique) **before** any component is written
- Build the five routes; landing page and `/dashboard` can ship before the AI layer is final
- `/ask` wired to the API once Gate 4 passes; `/evals` renders from committed result files
- Accessibility and mobile pass; empty and error states designed
- Deploy to Vercel on the target subdomain; preview deploys on every PR

**Gate 4b criteria:** site live · **ninety-second test passes with a real person who hasn't seen the project** · Lighthouse accessibility ≥ 95 · works at 380px · zero hardcoded numbers anywhere in the UI · repo linked from every page · design plan documents what was revised away from the generic default and why.

### Phase 5 — Publication · **Week 8**
**Lead:** Chief of Staff · **Primary:** `technical-writer`, `recruiter-lens-reviewer`, `release-manager`
- Five public artifacts finalised (§8)
- Architecture write-up published
- Demo video recorded (3–5 min, unedited walkthrough, real queries including one it refuses)
- Resume bullets drafted from **verified** numbers only, handed to the CEO for the master LaTeX resume
- Repo made public; README final; licences and attributions rendered

**Gate 5 criteria:** all five artifacts live and linked from `ishaaqkarim.dev` · every public number traceable to a committed run · recruiter-lens pass #3 clean · security sign-off on the public repo · **`docs/build-plan.md` gitignored and removed from the working tree (§0.1 ruling)** · CEO final approval.

### Post-launch (ongoing)
- Weekly CI refresh keeps the dashboard live — a stale dashboard is worse than none
- Source-liveness check opens issues automatically
- **DP-600** study begins after PL-300 completes; the Fabric work is the practical grounding

---

## 7. Repository structure

```
GTA-Housing-pipeline/             # github.com/Halomaster0/GTA-Housing-pipeline (public, MIT)
├── README.md
├── LICENSE                       # MIT
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── Makefile
├── pyproject.toml
├── .env.example
├── .claude/
│   └── agents/                   # one file per role card in §5
├── .github/
│   ├── workflows/
│   │   ├── pr.yml
│   │   ├── pipeline.yml
│   │   ├── verify-sources.yml
│   │   └── web.yml               # lint, build, a11y check on the app
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
├── src/
│   ├── ingest/                   # connectors, base class, drift detection
│   ├── transform/                # DuckDB runner
│   ├── ai/
│   │   ├── planner.py
│   │   ├── executor.py
│   │   ├── critic.py
│   │   ├── retrieval/            # embeddings, hybrid search, text-to-SQL
│   │   └── graph.py              # the orchestration runtime
│   ├── api/                      # FastAPI: /ask, /status, /evals/latest
│   └── common/                   # config, logging, tracing, cost
├─ web/                          # Next.js public app → URL decided at Gate 4b
│   ├── app/
│   │   ├── page.tsx              # landing + live pipeline status
│   │   ├── ask/                  # NL query console
│   │   ├── dashboard/            # Power BI embed
│   │   ├── evals/                # live scorecard from committed results
│   │   └── architecture/         # MDX write-up
│   ├── components/
│   └── styles/tokens.css         # the design-lead token system
├── models/
│   ├── silver/*.sql
│   └── gold/*.sql
├── tests/
│   ├── unit/
│   └── data/                     # data quality tests
├── evals/
│   ├── golden_questions.yaml
│   ├── harness.py
│   └── results/                  # versioned, committed
├── fixtures/                     # committed sample data for CI
├── traces/                       # sample traces committed, rest gitignored
├── scripts/
│   ├── verify_sources.py
│   └── reconcile.py
├── powerbi/                      # .pbip project files
└── docs/
    ├── charter.md
    ├── architecture.md
    ├── design-plan.md            # design-lead, approved before any UI code
    ├── schema-design.md
    ├── conformance-matrix.md
    ├── data-dictionary.md
    ├── data-quality-report.md
    ├── eval-report.md
    ├── fabric-setup.md
    ├── cost-log.md
    ├── sources/
    ├── decisions/                # ADRs
    ├── standups/
    ├── gates/
    ├── drift/
    └── reviews/
```

---

## 8. The five public artifacts

| # | Artifact | Location | Owner | Proves |
|---|---|---|---|---|
| 1 | **Public GitHub repo** — MIT, runnable from clean clone | `github.com/Halomaster0/GTA-Housing-pipeline` | `oss-maintainer` + `cicd-engineer` | Engineering discipline, reproducibility, open-source literacy |
| 2 | **Live Power BI dashboard** — refreshing weekly | `/dashboard` | `report-builder` | BI depth, PL-300 competence, real serving layer |
| 3 | **Live NL query console** — citations, SQL, traces | `/ask` | `agent-orchestration-engineer` + `frontend-engineer` | AI engineering, RAG, multi-agent orchestration |
| 4 | **Published eval report** — real scores, weak buckets named | `/evals` | `eval-engineer` | The differentiator. Almost nobody does this. |
| 5 | **Architecture write-up** — decisions and trade-offs | `/architecture` | `technical-writer` | Judgement, seniority, communication |

**The web app is the front door; the repo is the proof.** Artifacts 2–5 live inside the app, so one link from a resume reaches all of them. Every page links to the repo, and the README links back to every page.

---

## 9. Risk register

| # | Risk | Owner | Mitigation | Trigger to escalate |
|---|---|---|---|---|
| R1 | A source is retired mid-build | `source-scout` | Weekly liveness CI; fetch canonical pages directly, never trust search results | Any verify-sources failure |
| R2 | Fabric trial lapses | `fabric-architect` | DuckDB remains source of truth; Fabric is serving only; local demo path always works | 2 weeks before expiry |
| R3 | Cross-municipality definitions don't conform cleanly | `transform-engineer` | Conformance matrix + ADRs; document irreconcilable differences rather than papering over them | Any metric whose meaning changes |
| R4 | AI layer becomes a demo, not a system | `director-ai` | Eval-first sequencing; anti-pattern watchlist; traces required | Eval written after implementation |
| R5 | LLM cost overruns | `cost-controller` | Local embeddings; cached classification; eval subset in CI; hard budget | 50% of budget consumed |
| R6 | Scope creep | `chief-of-staff` | Non-goals in §1 are binding; new ideas go to `docs/backlog.md`, not into the build | Any new feature proposed mid-phase |
| R7 | Prompt injection via public free-text fields | `security-and-licence-reviewer` | Treat source text as untrusted; read-only SQL role; query validation | Before demo goes public |
| R8 | Timeline slips past 8 weeks | `chief-of-staff` | Phases 4 and 5 are the differentiators — cut report pages before cutting eval. **CEO confirmed this original order at Gate 0 (2026-09-10)** even though the stated target role is Analytics Engineering / BI; revisit at Gate 3 with real velocity data | End of week 5 with Gate 3 open |
| R9 | A secret lands in public git history | `oss-maintainer` | Pre-commit secret scanning; history scanned at every gate; `.env.example` only | Immediately, to CEO — rotate **and** rewrite history same session |
| R10 | Public `/ask` endpoint drives runaway LLM spend | `api-engineer` | Per-IP limits, global daily ceiling, aggressive caching, cached fallback answers when capped | Any day exceeding 10% of monthly budget |
| R11 | The site reads as "another Next.js app" | `recruiter-lens-reviewer` | Landing page leads with the pipeline and eval evidence, not the UI; README frames the app as a thin client | Any recruiter-lens pass flagging it |
| R12 | Frontend polish eats time budgeted for eval | `chief-of-staff` | Phase 4b is timeboxed; five routes is the ceiling, not the floor. A plain site with a real eval report beats a beautiful site without one | Any design iteration past week 7 |

---

## 10. Resume bullet candidates (draft only — fill from real results at Gate 5)

Do not use these until the numbers exist. Blanks stay blank until measured.

- Built a multi-source data platform ingesting GTA municipal open data (Toronto CKAN, Peel/Mississauga/Brampton ArcGIS, StatCan) into a dimensional warehouse — **___** rows across **___** conformed tables, refreshed weekly via CI with automated data-quality and schema-drift checks.
- Designed a multi-agent RAG query layer (planner → executor → critic) over the warehouse combining text-to-SQL, hybrid semantic retrieval, and tabular QA, returning cited rows and executed SQL with every answer.
- Built a scored evaluation harness over **___** golden questions measuring correctness, faithfulness, retrieval recall, and refusal accuracy — CI-gated against regression, results published publicly.
- Modelled and published a Power BI semantic layer on Microsoft Fabric with **___** documented measures, powering a public dashboard covering **___** GTA municipalities.

`recruiter-lens-reviewer` finalises these at Gate 5. Every blank gets a number from a committed run, or the clause gets deleted.

---

**End of plan. Version 1.0. Amend via ADR.**
