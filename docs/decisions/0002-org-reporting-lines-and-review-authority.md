# ADR-0002: Reporting lines and review authority, where the plan was ambiguous

Status: Accepted · Date: 2026-09-10 · Decider: Chief of Staff · Reviewed by: CEO at Gate 0

## Context

Generating the 26 agent definitions from §5 of the build plan surfaced five places where §3 (org chart), §4 (operating protocol), §5 (role cards) and §6 (phase plan) do not agree, or are silent. Left unresolved, each becomes a recurring argument between agents, or worse, a silent gap where nobody reviews something.

## Options considered

Resolve each ambiguity inside the individual agent file, and let the inconsistency persist across files; or rule once, centrally, and have every agent file point here. The first is faster and produces 26 subtly different interpretations of the same org.

## Decision

### 1. `api-engineer` reports to `director-product-frontend`

§3 places `api-engineer` under Director of Product & Frontend. §6 Phase 4 step 6 has it wrapping the AI query graph, which reads as AI-track work.

Ruling: `api-engineer` reports to **`director-product-frontend`**, because what it actually owns is a contract — the interface the web app consumes, plus the abuse and cost surface of a public endpoint. Two mandatory co-reviews attach to it:

- **`director-ai` co-reviews** anything touching `src/ai/graph.py` invocation or SQL execution safety. The API must not weaken the read-only execution guarantees the AI layer establishes.
- **`security-and-licence-reviewer` blocks** public exposure until it signs off, per §5.21. This is not a courtesy review.
- **`cost-controller` must sign off** on the rate limit and daily spend ceiling before the endpoint is reachable publicly (risk R10).

### 2. Directors have a definition of done, even though §5 gives them none

§5.2, §5.7, §5.10 and §5.14 give Directors review checklists but no definition of done. A reviewer with no DoD reviews inconsistently.

Ruling: a Director's work for a phase is done when **every merged PR in its domain carries the Director's full checklist, pasted, with evidence against each line**. Evidence is a file path or command output. A ticked box with nothing behind it is a failed review, and `release-manager` treats it as an unmet gate criterion.

### 3. `data-quality-auditor` audits independently of PR review state

§6 Gate 2 says the auditor "signs off". §4 says it holds an independent veto. The two never say whether it runs before or after Director review.

Ruling: the auditor runs its **own audit regardless of review state**, on whatever is on the branch, and its veto **survives a Director approval**. It does not queue behind Director review and it is not required to wait for one. Only the CEO overrides a veto, and an override is recorded in the gate file.

### 4. Conformance escalation has a threshold

§5.5 sends conformance decisions from `transform-engineer` to its Director. §5.2 sends them from the Director to Chief of Staff plus an ADR. Read literally, every column mapping becomes a Chief of Staff escalation.

Ruling: two tiers.

- **Mechanical conformance** (a field rename, a type cast, a unit conversion with one obvious correct answer) is settled between `transform-engineer` and `director-data-engineering`, documented in the SQL comment and a row in `docs/conformance-matrix.md`. No ADR.
- **Semantic conformance** — anything that changes what a published metric *means*, or where two municipalities' definitions cannot both be honoured — goes to Chief of Staff and gets an ADR. Irreconcilable differences are documented as irreconcilable rather than papered over (risk R3).

The test: *would a BI consumer reading the measure definition get a different answer because of this choice?* If yes, it is semantic.

### 5. `chief-of-staff` bootstrap when its inputs do not exist

Its session-open ritual reads the last standup and the current gate file. On session 1 neither exists.

Ruling: when an input is missing, `chief-of-staff` states so explicitly ("no prior standup; charter not yet signed") and proceeds. It never blocks on a missing artifact of its own, and never invents the contents of one.

## Consequences

- Every agent file's Escalation section is consistent with a single org model.
- `api-engineer` has three sign-offs to clear before its endpoint goes public. That is deliberate friction on the one surface that can spend money unboundedly.
- The two-tier conformance rule keeps `docs/decisions/` meaningful. An ADR directory with forty entries about column renames is an ADR directory nobody reads.

## Revisit if

A Director's checklist proves unreviewable in practice, or the conformance threshold produces an argument about which tier a decision falls into more than once.
