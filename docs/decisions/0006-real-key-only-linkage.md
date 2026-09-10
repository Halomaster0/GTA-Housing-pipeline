# ADR-0006: Permit–application linkage is real-key-only, never inferred

Status: Accepted · Date: 2026-09-10 · Decider: `director-data-engineering` · Reviewed by: Chief of Staff

## Context

The golden eval set names a question that needs this link ("how has
Brampton's application-to-permit time changed since 2019?"). Live field
capture (2026-09-10) shows what keys actually exist:

- Toronto applications carry `FOLDERRSN` as **text** (e.g. `5060317`).
- Brampton production permits carry `FOLDERRSN` as **double**. Same name,
  different type, different municipality — a lead, not proof of a shared key
  space (Director ruling §8-3).
- Mississauga permits carry `BP_NO` only — no `FOLDERRSN`.
- Brampton planning layers (Minor Variance sample) carry `FILE_NUMBER` with
  no `FOLDERRSN`, no unit fields, no decision date.
- Toronto permits carry `PERMIT_NUM` with no application cross-reference
  field at all.

So the only candidate cross-table key in the entire model is a
same-named, differently-typed field across two different municipalities'
systems, unproven to share a key space. Everything else has no key to follow.

## Options considered

1. Real-key-only: follow an explicit published cross-reference where one
   exists and is proven; otherwise leave the link null (adopted, per
   Director ruling §8-3).
2. Opt-in heuristic join (address + date proximity) to make the golden
   question answerable. Rejected: an unvalidated join produces
   plausible-looking but unvalidated durations — the exact failure the
   faithfulness metric exists to catch. The eval harness's refusal-accuracy
   bucket exists precisely to reward refusing this question when the key is
   absent.
3. Treat same-named `FOLDERRSN` as a shared key without proof. Rejected: a
   type mismatch across municipal systems is evidence *against* a shared key
   space, not for one.

## Decision

- `fct_permits.related_application_number` is populated **only** from an
  explicit source-published cross-reference proven to resolve within the same
  municipality's application entity. No address/date-proximity inference, no
  cross-municipal key matching, no exceptions in v1.
- Phase 2 evaluates the `FOLDERRSN` lead honestly: same-municipality
  resolution test only (does any Toronto permit carry a Toronto-application
  `FOLDERRSN`? does any Brampton application carry a Brampton-permit
  `FOLDERRSN`?). The Toronto↔Brampton same-name coincidence is not tested as
  a join — different municipalities never share a key space without a
  published crosswalk, which does not exist.
- Metrics needing the link (application-to-permit time) compute **only**
  over the linked subset, reporting the excluded share alongside — or the
  query layer refuses with the reason stated ("no published linking key"),
  which scores as correct refusal, not failure.
- The golden eval question on Brampton timing stays in the set regardless:
  if unlinkable in v1, its expected behaviour is refusal, and that is
  written into the case file before tuning (eval-first sequencing, risk R4).

## Consequences

- The two fact tables are related-but-independent in v1, as the schema
  design assumed (A15). No dashboard page implies a joined pipeline that
  does not exist.
- A proven same-municipality `FOLDERRSN` resolution would upgrade this ADR
  by amendment with the resolution evidence attached — the door is open, the
  bar is proof.

## Revisit if

- A source publishes an explicit permit↔application cross-reference, or the
  Phase 2 key-resolution test proves a same-municipality `FOLDERRSN` key
  space with measured match rates.
- The eval harness shows the refusal bucket punishing a question users
  reasonably expect answered — then the remedy is better refusal copy and
  subset metrics, not a heuristic join.
