# Repository metadata

These are GitHub repository settings that cannot be applied from inside the repository itself — they live in GitHub's settings UI and need a human with admin access (the CEO) to apply them. This document is the source of truth for what those settings should be; when they're set, they should match this file, not drift from it.

## Repository description

Paste exactly into **Settings → General → Description**:

```
Public data + AI platform over Greater Toronto Area housing and development data: municipal open-data ingestion, a DuckDB dimensional warehouse, a Power BI serving layer, and a multi-agent RAG query system with a scored evaluation harness. Built in the open.
```

Keep this in sync with the README's opening two sentences if either changes — they should never contradict each other.

## Topics

Paste into **Settings → General → Topics** (one topic per box, GitHub topics are lowercase with hyphens):

```
data-engineering
analytics-engineering
rag
duckdb
microsoft-fabric
power-bi
llm-evaluation
open-data
toronto
python
```

## Social preview image

**Settings → General → Social preview.**

Not yet created — this is a placeholder until `design-lead` and `frontend-engineer` produce one. When it exists:

- Should be a static image (PNG/JPG), 1280×640px minimum, that reads correctly as a small thumbnail (link previews in Slack, Twitter/X, LinkedIn all crop and shrink it).
- Should show something real from the project — a piece of the architecture diagram, an actual dashboard screenshot, or an actual `/ask` response — not a generic logo or stock graphic. This project's whole posture is "verify, don't assert"; the preview image should hold to that.
- Should not include any number that isn't backed by a committed run, for the same reason nothing in the README does.
- Until a real one exists, leave the social preview unset rather than uploading a placeholder — an unset preview reads as "not finished yet," which is honest; a generic placeholder reads as finished and isn't.

## Pinned README

GitHub renders `README.md` at the repo root automatically — no separate action needed beyond keeping it current. If the CEO's GitHub profile pins repositories, this one should be among them once Phase 1's OSS scaffolding (this document included) is merged.

## Branch protection checklist (manual — apply in Settings → Branches)

Apply to `main` (or whichever branch is the default):

- [ ] **Require a pull request before merging** — direct pushes to the default branch are disabled, including for admins if the org tier supports it.
- [ ] **Require status checks to pass before merging** — at minimum, the PR CI workflow (lint, type-check, unit tests, data tests on fixtures) once `cicd-engineer`'s workflows exist; add the eval-subset check once Phase 4 lands.
- [ ] **Require branches to be up to date before merging**, so a passing check reflects the actual merge result, not a stale one.
- [ ] **Require conversation resolution before merging.**
- [ ] **No force-push to `main`** — force-pushes disabled on the protected branch. (The one narrow exception is the documented secret-in-history procedure in `SECURITY.md`, which is a deliberate, CEO-directed history rewrite, not routine practice.)
- [ ] **No branch deletion** for the default branch.
- [ ] Require signed commits — optional, but consistent with the "commits are readable and this history is a real evaluation surface" posture in the build plan; adopt if it doesn't create friction for a solo-plus-agents workflow.

None of the above is automatable from this repository's own files — GitHub's branch protection API requires admin credentials this project's agents don't hold. This checklist exists so it isn't forgotten and so Gate 1's "branch protection on" exit criterion has something concrete to check against.

## Milestones and issues

Per the build plan (§6), the phase plan should be mirrored into GitHub milestones (one per phase, matching the gate criteria in `docs/build-plan.md` §6) and issues (one per major workstream item under each phase). That mirroring is a `chief-of-staff` / repository-admin action using the GitHub UI or API directly, not a file this repository stores — this document just flags that it's an open Gate 1 exit criterion, not something already done.
