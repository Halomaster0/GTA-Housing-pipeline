# Cost log

**Owner:** `cost-controller` · **Budget ceiling:** CAD $50.00 (hard, set by CEO at Gate 0, 2026-09-10)
**Spent to date: CAD $0.00** · **Escalation trigger: CAD $25.00 (50%)**

Every dollar and every token that costs money is recorded here. A paid resource is never provisioned before its decision line exists in this log.

---

## Ledger

| Date | Item | Vendor | Amount (CAD) | CEO decision | Running total |
|---|---|---|---|---|---|
| 2026-09-10 | Budget ceiling set at Gate 0 | — | 0.00 | `docs/charter.md` §1 | 0.00 |
| 2026-09-11 | Fabric capacity via school account (replaces trial plan — no trial window, no conversion risk while enrolled) | school tenant | 0.00 personal | CEO decision in chat 2026-09-11; provisioning still gated on tenant capability check (HANDOVER-7 §2) | 0.00 |

No spend has occurred. This is a measured zero, not a placeholder.

---

## Free-tier inventory — what the project runs on at $0

| Layer | Choice | Cost | Expiry risk |
|---|---|---|---|
| Local warehouse | DuckDB | free, open source | none |
| Ingestion + transform compute | local / GitHub Actions | free (public repos get free Actions minutes) | none while the repo stays public |
| Embeddings | `sentence-transformers`, run locally | free | none — deliberately chosen over paid embedding APIs |
| Classification | HF `zero-shot-classification`, cached to a silver column | free | none — never called at query time |
| Vector store | LanceDB, local | free | none |
| Serving | Microsoft Fabric via school account (was: trial) | $0 personal while enrolled | lower than trial risk R2 but still borrowed — DuckDB stays the source of truth so losing access never breaks the build; keep coursework and project workspaces separate |
| Web hosting | Vercel Hobby | free | none for a non-commercial project |
| Domain | `ishaaqkarim.dev`, already owned by the CEO | $0 incremental | none |
| LLM | Anthropic API | **paid** — the only line item expected to draw on the budget | n/a |

## Where the budget will actually go

The only expected spend is Anthropic API usage, in three places:

1. **Eval runs.** Roughly 60 golden questions per full run, each running planner → executor → critic. Every run appends its measured cost here. CI runs a fast subset, not the full set, to keep per-PR cost near zero.
2. **The public `/ask` endpoint.** This is the runaway risk (R10). Mitigated in code, not policy: per-IP rate limiting, a global daily spend ceiling, aggressive caching on normalised question hashes, and cached example answers served with a plain explanation when the ceiling is hit.
3. **Development iteration** while tuning against the eval set.

## Rules

- Free or local is the default at every layer. Deviating requires a recorded CEO decision.
- Estimates are labelled as estimates and never counted in the running total.
- Every eval run appends its actual measured cost, including the runs that were wasteful.
- At CAD $25.00 consumed, `cost-controller` escalates to the CEO through `chief-of-staff` before further spend.
- If the Fabric trial would convert to paid, that is a CEO escalation **before** the conversion date, not after (risk R2).
