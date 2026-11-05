# ADR-0011: AWS analytics layer (S3, Glue, Athena), verified against DuckDB

Status: Accepted and implemented · Date: 2026-11-04 (deployed and verified 2026-11-05)
· Decider: project owner · Reviewed by: pending (the role-card sign-offs listed under
"Verification" are not yet recorded)

## Context

The project has no cloud-platform experience on record. Fabric serving (ADR-0008) is
deferred, and the school Power BI Pro workspace has no capacity (ADR-0010). The
project's cloud gap is therefore unproven, and that matters for the portfolio.

This ADR adds an **optional** AWS path beside the existing pipeline. The gold tables
are exported to Parquet, described by a Glue catalog, and queried with Athena. A
least-privilege reader role runs the queries, and a parity test checks the answers
against DuckDB. Nothing else changes: the warehouse, the query API, the eval harness,
the Vercel deployment and the web app stay as they are. No AWS resource is reachable
from the public site or `/ask`.

The account is a new-experience AWS account on the **FREE plan** with USD 100 of
credits (expiring 2027-05-04, checked 2026-11-04). The account Region is fixed by the
project to `us-east-2`.

## Options considered

1. **Do nothing.** Rejected. The cloud gap stays unproven.
2. **LocalStack only.** Rejected as the sole path. It emulates AWS, so it proves the
   Terraform and not the service behaviour, and it does not show a deployment. It may
   still be used later for fast iteration.
3. **Microsoft Fabric.** Deferred, as ADR-0008 and ADR-0010 already decided. No capacity
   is available on the school tenant.
4. **Redshift.** Rejected. A provisioned cluster has a fixed hourly cost that would
   consume the credits while idle, and it adds operational weight that the project
   does not need.
5. **Athena over S3 + Glue (chosen).** Serverless. It bills per byte scanned, so an
   idle deployment costs almost nothing. S3, Glue and Athena are all on the free-plan
   supported list.

## Decision

- **Storage:** one curated bucket for the gold Parquet under `gold/<table>/`, and one
  bucket for Athena results. Both block public access, use SSE-S3, enforce bucket
  ownership, and have `force_destroy` set. Result files expire after 3 days.
- **Catalog:** one Glue database and one explicit external table per gold table (7).
  No crawler. Column lists are generated from the Parquet schemas by
  `scripts/aws/gen_glue_schema.py`, so the Terraform cannot drift from the models. The
  generator fails on any Arrow type it does not map.
- **Query:** an Athena workgroup with enforced configuration and a 100 MiB per-query
  scan cutoff. The largest table is about 13 MB as Parquet, so a full scan is well
  inside the cutoff. A query that would exceed it is cancelled rather than billed.
- **Access:** `gta-housing-athena-reader`, assumable only by the deployer role. It reads
  the gold prefix, writes only the results prefix, reads one Glue database, and runs
  queries on one workgroup. It cannot write the curated bucket and cannot create or
  delete Glue tables.
- **Cost guardrail:** an AWS Budgets monthly budget that excludes credits, so it tracks
  gross usage. Alerts fire on actual spend at 50%, 80% and 100% of the limit.
- **Verification:** `tests/integration/test_athena_parity.py` assumes the reader role
  and compares Athena with DuckDB (see the parity section of the README). It is opt-in
  and skipped by default, so CI never reaches AWS.
- **Direction:** a one-way copy from DuckDB to S3. DuckDB stays the source of truth.

## Consequences

- The Terraform is reproducible from the repo, with a committed provider lock file and
  pinned Terraform (1.16.6) and AWS provider (6.x) versions.
- The published numbers are the **September** vintage only (see
  `docs/data-vintage-decision-2026-10-31.md`). The upload refuses to run unless the
  fact row counts match `docs/measure-reconciliation.json`.
- The budget excludes credits, so while credits last the budget will show spend that
  is covered by credits. The alert still fires on real usage.
- The Terraform state is local and never committed. Losing the machine loses the state,
  and a destroy then needs the console or a re-import. This is accepted for a
  verification deployment.

## Limits (what this does not prove)

- **Single account, single Region, local state.** No multi-account, no remote backend,
  no state locking.
- **One-way copy.** Athena reads a snapshot. It does not see later changes in DuckDB
  until the upload is run again.
- **Dependent on credits.** The FREE plan covers these services, but the deployment
  depends on the USD 100 of credits and their 2027-05-04 expiry. Behaviour after the
  credits run out is not verified here.
- **September vintage only.** No October data is published through this path.
- **Not production.** This is a deployment to a personal AWS account for verification.
  It is not a production data lake and does not claim scale or Athena performance.
- **Dialect differences.** Recorded in the parity report and the README as they are
  found. Only the queries the test runs are compared.

## Verification

Each item below is a required check. A line stays unchecked until its evidence exists.

- [ ] Stage 0 smoke test (bucket, Glue database, Athena workgroup, `SELECT 1`) passed
      and was torn down. Passed on 2026-11-04 in us-east-2 (run by the assistant at the
      owner's request; the brief assigns it to the owner).
- [x] `terraform fmt -check` and `terraform validate` pass (Terraform 1.16.6).
- [x] `terraform plan` reviewed: 22 to add, 0 to change, 0 to destroy (2026-11-04).
- [x] `terraform apply` run (2026-11-05, 22 added). Owner allowed the apply command.
- [x] Parity test passes (2026-11-05): row counts for all 7 tables, 3 measures, the
      43-row grouped aggregate, and the construction-value sum. 13 of 13 tests pass.
      Bytes scanned: 2,706,812 across 12 queries. Report: `docs/aws-parity-report.md`.
- [x] Negative tests pass: reader role denied `s3:PutObject` to the curated bucket,
      `glue:CreateTable`, and `glue:DeleteTable`.
- [x] Budget alerts exist and exclude credits: the Terraform budget reads back
      `IncludeCredit=false`, limit USD 5, actual alerts at 50, 80 and 100%
      (2026-11-05). The hand-made budget also has a credit-excluding filter.
- [x] Dialect differences: none found in the 13 queries run (counts, sums, a grouped
      count across two joins). Recorded as a finding, not a guarantee for other queries.
- [ ] `security-and-licence-reviewer` sign-off on IAM, public access and secrets.
- [ ] `cost-controller` sign-off on the budget and the scan cutoff.
- [ ] `data-quality-auditor` sign-off on the parity test.
- [ ] `security-and-licence-reviewer` sign-off on IAM, public access and secrets.
- [ ] `cost-controller` sign-off on the budget and the scan cutoff.
- [ ] `data-quality-auditor` sign-off on the parity test.

## Revisit if

The FREE plan stops covering any of these services, the credits expire without a paid
plan, the project gains a Fabric capacity (ADR-0008 path), or the parity test finds
a real divergence from DuckDB.
