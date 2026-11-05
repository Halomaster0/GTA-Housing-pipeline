# AWS parity report

Generated 2026-11-05 00:22 UTC by `tests/integration/test_athena_parity.py`.

Athena runs as a least-privilege reader role against the September gold tables. DuckDB (`data/warehouse-sept.duckdb`) is the source of truth.

## Athena queries

| Check | Query ID | State | Bytes scanned | Engine ms |
| --- | --- | --- | ---: | ---: |
| count dim_date | `f74d6836-bcd7-4a2b-b922-d1b57bef0bb9` | SUCCEEDED | 0 | 407 |
| count dim_municipality | `a7fee97a-e297-4590-a28c-9676c628897c` | SUCCEEDED | 0 | 435 |
| count dim_geography | `282dd1d4-34b6-40bb-8d27-38a36e6d1dd0` | SUCCEEDED | 0 | 354 |
| count dim_use_type | `d229bdc5-bf18-42b4-ae3e-1d4e4cbfe463` | SUCCEEDED | 0 | 372 |
| count dim_status | `9cc3e387-f783-4511-bda1-6c0d3f58ace5` | SUCCEEDED | 0 | 364 |
| count fct_permits | `475d5482-3a3e-44c4-8f3c-26bdd3e40091` | SUCCEEDED | 0 | 449 |
| count fct_applications | `cb9a9713-6fcc-4e1c-90af-b3773bee1c27` | SUCCEEDED | 0 | 451 |
| anchor permit records | `135d5a6d-68b6-415b-b305-3b82f7500e6d` | SUCCEEDED | 0 | 460 |
| anchor applications | `2a8840a9-b453-4561-b91e-392c0f9fc3e9` | SUCCEEDED | 0 | 397 |
| anchor permits issued | `7551135b-539e-46d6-875a-08fe36b7515b` | SUCCEEDED | 1,098,500 | 940 |
| issued by municipality and year | `ef786ff8-9e09-405a-a3c0-b145b98df996` | SUCCEEDED | 1,127,402 | 1,663 |
| construction value sum by municipality | `d4087c0b-3112-4993-bb3f-329dc6fe20ba` | SUCCEEDED | 480,910 | 1,290 |

Total bytes scanned across 12 queries: **2,706,812** (2.707 MB).

## Negative tests (reader role)

| Attempted action | Observed error |
| --- | --- |
| s3:PutObject to the curated bucket | AccessDenied |
| glue:CreateTable | AccessDeniedException |
| glue:DeleteTable (nonexistent probe name) | AccessDeniedException |
