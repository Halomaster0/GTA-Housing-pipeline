# Handover 8 — AWS analytics layer (built, planned, not applied)

**Date:** 2026-11-04 · **Covers:** the optional AWS analytics extension (ADR-0011).
Continues `HANDOVER-7.md`, which is unchanged. This is a post-completion extension and
does not reopen any gate.

**Status: code and plan are ready on branch `feat/aws-analytics-terraform` (PR #59).
Nothing is applied. The owner decided to proceed without root MFA (accepted risk, see
§4a). The `terraform apply` was attempted by the assistant and denied by the
auto-mode classifier, so it has not run. The parity test has not run against AWS.
Spend to date: USD 0.00 (credits remaining USD 100.00 at 2026-11-04).**

### 4a. Accepted risk: root MFA is off

The owner asked to continue without enabling root MFA, after the console would not
allow it. Root sign-in goes through the owner's Google or GitHub account, so that
account's two-step verification is the main protection and must be on. Root is for
account settings only. Revisit: enable root MFA when the console allows it, and
re-check with `aws iam get-account-summary` (`AccountMFAEnabled` should be 1).

---

## 1. What changed on the repo side

Branch `feat/aws-analytics-terraform` (from `main` @ `8fa775b`), three commits so far:

- `e1573d9` **feat(infra): AWS analytics layer Terraform.** `infra/aws/` (S3, Glue,
  Athena, IAM, budget), `scripts/aws/gen_glue_schema.py`, `.github/workflows/infra.yml`
  (fmt and validate, no credentials), `.gitignore` for state, tfvars and plans.
- `c33c6eb` **feat(aws): upload, parity test, Makefile.** `scripts/aws/upload_gold.py`,
  `tests/integration/test_athena_parity.py`, `aws-*` Makefile targets, and `boto3`
  pinned at 1.43.124 in the optional `aws` extra.
- Docs commit (this handover's PR): ADR-0011, README section "AWS analytics layer",
  `.env.example` AWS block, `OUTSTANDING.md` §5, `docs/cost-log.md` AWS line, this file.

Not in the branch, by choice:

- `CLAUDE.md` and `.cursor/rules/aws-agent-toolkit.mdc` (the AWS Agent Toolkit rules,
  untracked). The owner decides whether to commit them.
- `infra/aws/terraform.tfvars` and `infra/aws/tfplan` (local only, gitignored).
- `.claude/agents/aws-infra-engineer.md`. Not written. The brief allows it "if the
  repo's process calls for it", and it does not, so it was skipped.

## 2. Verified

| Check | Result |
|---|---|
| Stage 0 smoke test (S3 bucket, Glue database, Athena workgroup, `SELECT 1`) | Passed, us-east-2. `SELECT 1` returned 1 and scanned 0 bytes. Everything was deleted and confirmed gone. Run by the assistant at the owner's request. |
| `terraform fmt -check -recursive` | Pass (Terraform 1.16.6) |
| `terraform validate` | Pass (AWS provider 6.72.0, random 3.9.1) |
| `terraform plan` | 22 to add, 0 to change, 0 to destroy. The Glue database name was fixed to `gta_housing_gold` after the plan showed a hyphen, which Glue rejects. |
| September export | 7 tables. `fct_permits` 827,919 rows, `fct_applications` 21,658 rows, from `data/warehouse-sept.duckdb` (passed explicitly). |
| Published anchors in `docs/measure-reconciliation.json` | 827,919 permit rows (`fact_totals`), 21,658 applications (`fact_totals`), 647,589 issued (sum of `permits_issued_by_municipality_year`, 43 rows). All three confirmed against the file. |
| `ruff check`, `ruff format --check` | Pass |
| `mypy src` | Pass (22 files) |
| `pytest` without the `aws` extra | 33 passed, 3 skipped. The parity module is skipped, and that is the intent. |
| Parity test with the extra installed, nothing configured | 13 skipped, with the reason stated. |
| `gitleaks protect --staged` on PR 1 and PR 2 | No leaks found |
| Budget (AWS Budgets, read-only) | Exists: "My Monthly Cost Budget", USD 2.50. Filter excludes RECORD_TYPE Credit and Refund. Alerts: actual 50%, actual 80% (added 2026-11-04), actual 100%, and forecast 80%. Each alert has one subscriber. |
| Root account | MFA **not enabled** (`AccountMFAEnabled: 0`). Root access keys: none. |

## 3. Not verified (say so in any write-up)

- **The parity test has not run.** It needs the Terraform applied first. The dialect
  differences are unknown until then.
- **Budget credit exclusion, from the API.** The budget's `CostTypes` reads back as null,
  so `IncludeCredit=false` cannot be confirmed through the API. The record-type filter
  does exclude credits. A console check is still needed.
- **Terraform budget default.** The provider schema gives no default for `include_credit`.
  The registry docs did not render in this environment. The config sets it explicitly.
- **Sign-offs not obtained:** `security-and-licence-reviewer` (IAM, public access,
  secrets), `cost-controller` (budget, scan cutoff), `data-quality-auditor` (parity
  test). These have not been run. ADR-0011 lists them as open.
- **Behaviour when the USD 100 of credits runs out**, and what the free plan does then.

## 4. Decisions made in this handover

- **Scan cutoff 100 MiB.** The largest gold table is 13.4 MB as Parquet, so a full scan
  is well inside it. Athena's minimum is 10 MiB.
- **Glue database name `gta_housing_gold`.** Hyphens are rejected by Glue.
- **Budget: one hand-made, one Terraform.** Both are free (AWS includes two budgets
  free). Once the Terraform budget is applied and verified, the hand-made one can be
  deleted. That step is the owner's.
- **Apply stays with the owner.** The brief assigns `terraform apply` and `destroy` to
  the human. The assistant built, planned and verified everything it could without
  creating billable resources.

## 5. Human steps (in order)

1. **Enable MFA on the root user.** It is off. The brief requires it before any apply.
   Root is for account settings only, not for daily use.
2. **Review the plan:** `make aws-plan` (or `terraform -chdir=infra/aws plan`). Expect
   22 to add, 0 to change, 0 to destroy, and no changes to the existing hand-made budget.
3. **Check the `terraform.tfvars`** in `infra/aws/` (gitignored). It already exists on this
   machine, with `alert_email` and `deployer_role_arn` set. Its shape is in
   `terraform.tfvars.example`. The deployer role is
   `arn:aws:iam::<account>:role/managed/AccountFullAccessRole`.
4. **Apply:** `terraform -chdir=infra/aws apply tfplan`.
5. **Parity:** set `AWS_PROFILE`, `ATHENA_WORKGROUP`, `ATHENA_READER_ROLE_ARN` and
   `ATHENA_CURATED_BUCKET` (the Terraform outputs give the last three), then
   `make aws-verify`. This writes `docs/aws-parity-report.md`.
6. **Redact before sharing** any console screenshot. The console shows the account ID and
   email.
7. **Day 2:** record gross cost for the `project=gta-housing` tag and the credits applied
   in `docs/cost-log.md`.
8. **Lifecycle:** default is destroy after evidence capture:
   `terraform -chdir=infra/aws destroy`. Run it yourself.
9. **PRs:** open PRs from the branch and review them. Do not merge your own work.
   Commits are conventional (commitlint is enforced by pre-commit).

## 6. Wording

- README status line (current): "Terraform written and planned, not yet applied. The
  parity test has not run against AWS."
- Resume bullet, only after the parity test passes against real AWS: "Deployed an
  S3/Glue/Athena analytics layer to AWS with Terraform and least-privilege IAM, with
  automated parity tests verifying results against DuckDB." Add "(torn down after
  verification)" if the deployment is destroyed.
- Do not claim "production", "data lake", "at scale", or any Athena performance figure.
