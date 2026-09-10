# Handover 1

**Date:** 2026-09-10 · **Branch:** `claude/gta-housing-build-plan-f0jhpo` · **16 commits, CI green**
**Status: Gate 0 closed. Gate 1 open.**

Detail lives elsewhere and is not repeated here:
`docs/charter.md` (the rulings) · `docs/standups/2026-09-10.md` (what shipped)
`docs/sources/evidence/2026-09-10-runner-discovery.md` (every confirmed fact)

---

## Completed

**Gate 0.** Charter signed. Budget starts at $0 with a CAD $50 ceiling; 10–15 hrs/week;
Analytics Engineering / BI as the target role; no subdomain until Gate 4b; the plan's
original cut order retained. The retired "atlas" codename was removed from every file.

**Phase 1, most of it.**

| Area | State |
|---|---|
| Agent org | 26 definitions in `.claude/agents/`, verified complete |
| Tooling | `pyproject.toml`, 114 packages locked on Python 3.11, Makefile, pre-commit with secret scanning |
| CI | Five workflows, all green |
| Open source | MIT licence, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, issue and PR templates, labels |
| README | Rewritten as the front door — no numbers, no dead links |
| Board | 42 GitHub issues: six gate trackers, 36 work items |
| Design | `docs/design-plan.md`, Pass 1 and self-critique, awaiting Director approval |
| Modelling | `docs/schema-design.md`, 25 falsifiable assumptions, 5 ADR-worthy conformance calls |
| Decisions | ADR-0001 tooling, ADR-0002 five org ambiguities resolved |
| Cost | **CAD $0.00**, measured |

**Sources.** This sandbox's network blocks every municipal and StatCan host, so verification
was moved onto GitHub runners, which are not blocked. **199 facts now confirmed from live
responses** — including Toronto applications at 26,613 rows, Mississauga permits at 34,615,
and StatCan's live product IDs. Nothing was recorded as confirmed while it was still a guess.

---

## Four things that need a decision

1. **Brampton publishes `_DEV` and `_UAT` copies of its layers publicly**, differing by up to
   3×, and the only permits service found is `Building_Permits_DEV`. Ingesting the wrong copy
   yields plausible wrong numbers nothing downstream would catch. Unresolved on purpose.
2. **Toronto's applications licence reads `License not specified`** — blocking, since it is
   the primary `fct_applications` feed.
3. **Caledon has no discovered permit feed.** Peel turned out not to be a permit source
   (684 rows). Either scope Caledon out explicitly or surface the gap — not silence.
4. **Time-sensitive: Toronto applications have no decision date.** Status history only exists
   if the daily refresh is snapshotted *from now on*. Every day of delay is history lost.

## Next, in order

1. Resolve the Brampton `_DEV` question before ingesting any Brampton row.
2. Confirm every licence.
3. Transcribe the 199 facts into `config/sources.yml`; calibrate `expected_min_rows`.
4. Director review of the schema design and the design plan. No SQL or UI code until then.
5. Cold clone drill, then `release-manager` writes `docs/gates/gate-1.md`.

## Needs you — not automatable here

Milestones, branch protection, applying `.github/labels.yml`, repo topics. Steps are in
`docs/repo-metadata.md`. Later: Fabric trial timing, and an Anthropic API key for Phase 4.

## Rules that do not bend

Every published number comes from a real run with a committed script and output. Evidence is
a file path or command output, never an assertion. No secrets, ever — the repo is public and
history is permanent. No agent marks its own work done.
