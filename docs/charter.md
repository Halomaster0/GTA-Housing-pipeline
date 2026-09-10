# Project charter — GTA Housing Pipeline

**Status:** Signed at Gate 0 · **Date:** 2026-09-10 · **Owner (CEO):** Ishaaq Karim
**Repository:** https://github.com/Halomaster0/GTA-Housing-pipeline — public, MIT licensed, from the first commit
**Governing document:** `docs/build-plan.md` (v1.0). This charter records the decisions Gate 0 required and does not restate the plan.

---

## What this project is

A production-shaped data and AI platform over Greater Toronto Area housing and development data. Municipal open data from four incompatible portals is ingested, conformed into a dimensional model, served through a BI semantic layer, and queryable in plain English with answers grounded in the underlying rows and scored by an evaluation harness.

Success is a public repo, a live dashboard, a live natural-language query console, a published eval report with real numbers, and an architecture write-up — such that a hiring manager can verify the depth in under ten minutes without talking to the CEO.

---

## Gate 0 decisions

### 1. Budget — hard ceiling CAD $50

The project starts at **$0** and runs on free tiers by default. The CEO procures funding as needed up to a **hard ceiling of CAD $50** for the whole 8-week build.

Rules `cost-controller` enforces:

- A free or local option is the default for every layer. Local embeddings over API embeddings. DuckDB over hosted warehouses. GitHub Actions over hosted orchestration.
- **No paid resource is provisioned without a CEO decision recorded in `docs/cost-log.md` first.** "Record it after" is not acceptable — the log entry precedes the spend.
- Escalate to the CEO at **CAD $25** consumed (50% of ceiling), per risk R5.
- Every eval run appends its actual measured cost to the log. Estimated costs are marked as estimates and never counted as actuals.
- The public `/ask` endpoint carries a hard daily spend ceiling in code, not just in policy (§5.20, risk R10).

### 2. Time available — 10–15 hours per week

The 8-week schedule in §6 of the plan holds as written. PL-300 study begins Week 3 as a parallel track at roughly 4–5 hrs/week, drawing on the semantic-model work rather than competing with it.

If actual velocity falls below this, `chief-of-staff` raises it at the next gate rather than silently extending phases.

### 3. Target role — Analytics Engineering / BI

This is the primary role the artifacts are aimed at. Practical consequences:

- The README leads with the dimensional model and the cross-municipality conformance problem, not with the web app.
- `recruiter-lens-reviewer` reads every artifact as an analytics-engineering hiring manager first.
- The star schema, `docs/conformance-matrix.md`, the semantic model, the DAX measure library, and `docs/data-dictionary.md` are load-bearing artifacts, not supporting ones.
- Data engineering and AI engineering remain secondary audiences. The eval harness stays in scope — it is the rarest thing in the project and it reads well to any technical audience.

### 4. Deployment URL — deferred

No subdomain for now. The app ships on the default Vercel deployment URL. The final address is decided at **Gate 4b**.

Until then, no public artifact prints a subdomain. A dead link in a portfolio repo is worse than no link. The internal codename "atlas" is retired and appears on no public surface.

### 5. Cut order under time pressure — the plan's original order stands

Risk R8 as written: Phases 4 and 5 are the differentiators; **cut Power BI report pages before cutting anything in the eval harness.**

The CEO confirmed this at Gate 0 despite the Analytics Engineering / BI target, on the reasoning that the project should be built out as planned and edited where needed rather than pre-optimised. `chief-of-staff` revisits this at Gate 3 with real velocity data, and does not re-open it before then.

### 6. Build-plan visibility — committed now, removed before launch

`docs/build-plan.md` stays in the repository during development because it is the source of truth every session and every agent reads. Before Gate 5 it is added to `.gitignore` and removed from the working tree.

`release-manager` verifies this as a Gate 5 criterion. `oss-maintainer` owns the removal. Note that removal from the tree is not removal from history: if the CEO wants it gone entirely, that is a history rewrite and must be decided **before** Gate 5, not after.

---

## Binding non-goals

Restated from §1 because they are the scope defence `chief-of-staff` enforces. New ideas go to `docs/backlog.md`, not into the build.

- Not a real-estate price prediction model. No forecasting claims of any kind.
- Not a startup. No auth system, no billing, no multi-tenancy.
- Not a scraper. Official APIs and open-data endpoints only.
- Not a notebook. If it doesn't run on a schedule, it isn't done.

---

## The rule that overrides convenience

Every number that reaches a README, a doc, the web app, or a resume bullet comes from an actual run against real data, with a committed script and a committed output file. No projected, illustrative, or estimated figures. If a number cannot be produced, the artifact says so.

"Evidence" means a file path or pasted command output. An agent's assertion is not evidence.

---

## Sign-off

| Role | Name | Date |
|---|---|---|
| CEO | Ishaaq Karim | 2026-09-10 |
| Chief of Staff | `chief-of-staff` | 2026-09-10 |

Amend this charter by ADR only.
