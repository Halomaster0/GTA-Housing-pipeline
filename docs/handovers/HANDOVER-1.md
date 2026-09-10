# Handover 1

**Written:** 2026-09-10 · **By:** chief-of-staff (Claude Code, acting CEO delegate)
**Covers:** project kickoff through Gate 0 and most of Phase 1
**Branch:** `claude/gta-housing-build-plan-f0jhpo` · **Status at handover: Gate 0 CLOSED, Gate 1 OPEN**

Read this first on resuming. Then `docs/build-plan.md` (the plan), `docs/charter.md`
(the CEO's rulings), and the most recent file in `docs/standups/`.

---

## 1. Where the project stands

Phase 1 of 5. Nothing is deployed, no data has been ingested, no warehouse exists,
no numbers have been measured. That is the expected state at this point in the plan
and every public artifact says so plainly.

The repository is public, MIT licensed, scaffolded, and has green CI.

---

## 2. What is done

### Gate 0 — charter (CLOSED)
The CEO answered all four charter questions. `docs/charter.md` records them:

| Decision | Ruling |
|---|---|
| Budget | Start at $0, hard ceiling CAD $50. No paid resource without a recorded CEO decision *first*. Escalate at $25. |
| Time | 10-15 hrs/week. The 8-week schedule holds as written. |
| Target role | Analytics Engineering / BI, primary. DE and AI engineering secondary. |
| Deployment URL | None yet. Ships on the default Vercel URL; subdomain decided at Gate 4b. The "atlas" codename is retired. |
| Cut order | The plan's original R8 order stands: cut report pages before cutting eval. Revisit at Gate 3. |
| Build plan visibility | Committed during development, gitignored and removed from the tree before Gate 5. Removal from the tree is not removal from history. |

### Phase 1 deliverables

- **26 agent definitions** in `.claude/agents/`, one per role card, frontmatter verbatim
  from the plan. Verified: all 26 present, names match filenames, all seven required
  sections present in each.
- **Tooling and CI**: `pyproject.toml` (114 packages resolved and locked on Python 3.11),
  `Makefile`, `.pre-commit-config.yaml` with gitleaks and commitlint, `.gitignore`,
  five workflows. Targets for unbuilt phases print the phase that will build them and
  exit 0 rather than faking success.
- **Open-source scaffolding**: LICENSE (MIT), CONTRIBUTING, CODE_OF_CONDUCT, SECURITY,
  three issue templates, a PR template carrying every Director's review checklist,
  `.github/labels.yml`, `docs/repo-metadata.md`.
- **README** rewritten as the front door. No numbers, no live links (nothing is
  deployed), everything unbuilt marked unbuilt, and the Next.js app explicitly framed
  as a thin client so the repo is not misread as a frontend project (risk R11).
- **`docs/design-plan.md`** — design-lead Pass 1 and the Pass 2 self-critique. Palette
  derived from zoning maps and survey drawings with computed WCAG contrast ratios.
  Awaiting `director-product-frontend` approval, which gates all UI code.
- **ADR-0001** (tooling choices) and **ADR-0002** (five org ambiguities resolved:
  who reviews `api-engineer`, Director definitions of done, the data-quality auditor's
  veto ordering, the conformance-ADR threshold, and chief-of-staff bootstrap).
- **`docs/cost-log.md`** opened. Actual spend to date: **CAD $0.00**, measured, not assumed.
- **GitHub issues**: six gate trackers created (#1-#6).

---

## 3. The one significant finding

**The development sandbox cannot reach any data source.** Its network egress
allowlist permits only developer tooling (GitHub, package registries, the Anthropic
API) and rejects every municipal, ArcGIS and StatCan host. This was confirmed twice
independently — once by `source-scout`, once directly — including a control test
where unrelated hosts failed identically while github.com succeeded.

`source-scout` handled this correctly: it recorded nothing as confirmed. No row
count, no field list, no licence. Every entry in `config/sources.yml` is
`unverified-blocked` with `expected_min_rows: 0` and `calibrated: false`.

**The workaround is in place and it works.** `verify-sources.yml` now also triggers
on changes to the source registry, so verification runs on a GitHub runner, which has
normal internet access. The first runner-side run returned **HTTP 200 from all ten
hosts** — the sources are alive.

**Do not trust the row counts from that first run.** They came from discovery probes
whose count paths were guesses: Toronto reported 8 for wards when the city has 25,
and the six-figure ArcGIS figures are hub-wide catalogue totals, not permit counts.
`scripts/discover_sources.py` plus `.github/workflows/source-discovery.yml` were
added to resolve the real dataset identifiers, row totals, field names and licence
strings, printing raw response shapes to the job log for transcription by hand.

---

## 4. What must happen next, in order

1. **Read the source-discovery job log** and transcribe real dataset ids, row counts,
   field lists and exact licence names into `config/sources.yml` and
   `docs/sources/*.md`. Nothing becomes fact until a person has read the response it
   came from.
2. **Calibrate `expected_min_rows`** from observed counts and set `calibrated: true`.
   Never raise a threshold to make CI pass.
3. **Confirm every licence.** Not one is confirmed. An unconfirmed licence blocks
   public portfolio use exactly like an ambiguous one.
4. **Resolve the Peel question.** Peel is an upper-tier municipality and probably does
   not issue building permits at all — Mississauga, Brampton and Caledon do. Confirm
   before modelling Peel as a permit source.
5. **`director-data-engineering` reviews `docs/schema-design.md`**; `director-product-frontend`
   approves `docs/design-plan.md`. No SQL and no UI code before those approvals.
6. **Cold clone drill**, then `release-manager` writes `docs/gates/gate-1.md`.

---

## 5. Manual steps only the CEO can do

These are not automatable from this environment and are genuinely blocked on you:

- **Create GitHub milestones.** No milestone-creation tool exists in the available
  tooling. The phase plan is mirrored with `phase-1`..`phase-5` labels instead.
- **Turn on branch protection** on `main`: require a PR, require CI to pass, no
  force-push. See `docs/repo-metadata.md`.
- **Apply `.github/labels.yml`** to normalise label colours (labels auto-created by
  the API get default colours).
- **Set the repository description, topics and social preview.** Strings are in
  `docs/repo-metadata.md`.

---

## 6. Open questions for the CEO

1. **Fabric access.** Phase 3 needs a Microsoft Fabric trial. Starting it begins a
   clock (risk R2) and eventually costs money, which the CAD $50 ceiling does not
   comfortably cover. Decide when to start the trial so it does not lapse mid-Phase-3.
2. **Anthropic API key.** Phase 4 needs one. It goes in `.env`, never in the repo.
3. **Whether the build plan should ever be scrubbed from git history**, not merely
   removed from the tree. It must be decided before Gate 5, because after that the
   history is public and rewriting it breaks every clone.

---

## 7. Rules that must not be relaxed

- Every number in any public artifact comes from a real run, with a committed script
  and a committed output file. If it cannot be produced, the artifact says so.
- Evidence is a file path or pasted command output. An assertion is not evidence.
- No secrets, ever, not even briefly. The repository is public and history is forever.
- No agent marks its own work done.
