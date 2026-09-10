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
- **GitHub issues**: 42 open — six gate trackers (#1-#6) and 36 work items (#7-#42)
  mirroring the phase plan.
- **`docs/schema-design.md`** — the star schema drafted on paper, with 25 falsifiable
  assumptions and five conformance decisions classified as ADR-worthy.
- **`scripts/discover_sources.py`** and `.github/workflows/source-discovery.yml` — source
  reconnaissance that runs where the network actually reaches.

---

## 3. Sources: blocked locally, resolved on a runner

**The development sandbox cannot reach any data source.** Its egress allowlist permits only
developer tooling and rejects every municipal, ArcGIS and StatCan host. Confirmed twice
independently, including a control test where unrelated hosts failed identically while
github.com succeeded.

`source-scout` handled this correctly and recorded nothing as confirmed.

**The workaround works and is now the standard path.** `verify-sources.yml` and
`source-discovery.yml` run the checks on GitHub runners, which have normal internet access.
Three discovery passes have run. All ten hosts answer HTTP 200 and **199 facts** are now
confirmed from live responses. Full detail:
`docs/sources/evidence/2026-09-10-runner-discovery.md`.

### The feeds, with real row counts

| Source | Layer | Rows |
|---|---|---|
| Toronto | `development-applications` | 26,613 |
| Toronto | `city-wards` | 25 |
| Mississauga | `Issued_Building_Permits/0` | 34,615 |
| Mississauga | `Site_Plan_Applications/0` | 1,138 |
| Mississauga | `Rezoning_Applications/0` | 290 |
| Brampton | `Building_Permits_DEV/0` | 141,886 |
| Brampton | `Planning_Land_Use_Development` "Minor Variance" | 6,989 |
| Peel | `MunicipalBoundary_Peel/0` | 3 |
| Peel | `Building_Permits/0` | 684 |
| StatCan | active cubes listed | 8,270 |

StatCan product ids confirmed active: **34100292** building permits, **34100143** and
**34100148** CMHC housing starts, **98100002** dwelling counts by census subdivision,
**98100014** by census tract.

### Seven findings, worst first

1. **Brampton publishes `_DEV` and `_UAT` copies of its layers publicly**, with row counts
   differing by up to a factor of three (Minor Variance: 6,989 / 5,117 / 6,046). The only
   Brampton permits service found is `Building_Permits_DEV`. Pointing ingestion at the wrong
   copy yields plausible wrong numbers that nothing downstream would catch, because every
   individual row is valid. **Resolve before ingesting any Brampton row.**
2. **The Toronto applications licence is `License not specified`** — blocking, since that is
   the primary `fct_applications` feed.
3. **That dataset carries `CONTACT_NAME`, `CONTACT_PHONE`, `CONTACT_EMAIL`.** Dropped bronze
   to silver, enforced by a data test rather than a convention.
4. **It has no decision date and no unit count.** Status is a point-in-time snapshot, so
   status history only exists if the daily refresh is snapshotted from now on. It cannot be
   reconstructed later — every day of delay is a day of history lost.
5. **Peel is not a permit source.** 684 rows is not a register for 1.5 million people. Peel
   is geography and demographics. Consequently **Caledon has no discovered permit feed** and
   must not be silently dropped from a "GTA" claim.
6. **Ward vintages overlap**, confirming `dim_geography` must key on boundary version, not
   ward number.
7. **Mississauga publishes three parcel layers and three zoning layers** differing by small
   but answer-changing amounts. Pick one each, record the rest as rejected.

**CMHC is resolved.** StatCan republishes CMHC housing starts as 34100143 and 34100148 under
a documented API, so CMHC stays NOT ADOPTED as a direct source and no scraping is needed.

---

## 4. What must happen next, in order

1. **Resolve the Brampton `_DEV` question.** Find the production permits layer or establish
   that `_DEV` is the public feed. Nothing Brampton gets ingested until this is settled.
2. **Confirm every licence**, starting with Toronto applications. Nothing reaches a public
   artifact before its licence is named.
3. **Transcribe the 199 confirmed facts** into `config/sources.yml` — real ids, real
   `check_url`s, real `count_json_path`s — and calibrate `expected_min_rows` from observed
   counts, setting `calibrated: true`. Never raise a threshold to make CI pass.
4. **Decide whether to start snapshotting Toronto applications daily now**, given finding 4.
   This is the only item on the list that gets worse with delay.
5. **`director-data-engineering` reviews `docs/schema-design.md`** and
   **`director-product-frontend` approves `docs/design-plan.md`**. No SQL, no UI code before
   those approvals.
6. **Cold clone drill**, then `release-manager` writes `docs/gates/gate-1.md`.

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
4. **Caledon.** It is one of Peel's three municipalities and has no discovered permit feed.
   Either it is documented as out of scope, or the gap is surfaced in the model. Both are
   defensible; silently omitting it from a "GTA" claim is not.
5. **Daily snapshots of Toronto applications.** Status history cannot be reconstructed
   retroactively. Starting now costs almost nothing; starting at Phase 2 loses the interval.

---

## 7. Rules that must not be relaxed

- Every number in any public artifact comes from a real run, with a committed script
  and a committed output file. If it cannot be produced, the artifact says so.
- Evidence is a file path or pasted command output. An assertion is not evidence.
- No secrets, ever, not even briefly. The repository is public and history is forever.
- No agent marks its own work done.
