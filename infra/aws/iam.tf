# Least-privilege reader role for the Athena parity test and any read-only query.
#
# Trust: only var.deployer_role_arn (your SSO or deployer role) may assume it.
# Permissions: read the curated gold prefix, write only the results prefix, read this
# one Glue database and its tables, and run queries on this one workgroup.
# It cannot write to the curated bucket and cannot create or delete Glue tables.
#
# Wildcards: the only ones are the Glue table ARN (table/<db>/*), which is scoped to
# this database, and the S3 object paths below, which are scoped to one prefix each.

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.region
}

resource "aws_iam_role" "athena_reader" {
  name                 = "${var.name_prefix}-athena-reader"
  max_session_duration = 3600

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowDeployerToAssume"
      Effect    = "Allow"
      Principal = { AWS = var.deployer_role_arn }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "athena_reader" {
  name = "${var.name_prefix}-athena-reader-policy"
  role = aws_iam_role.athena_reader.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Listing the curated bucket, limited to the gold/ prefix.
        Sid      = "ListCuratedGoldPrefix"
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.curated.arn
        Condition = {
          StringLike = { "s3:prefix" = ["gold/*"] }
        }
      },
      {
        # Reading the gold Parquet files. Read-only: no Put, Delete or Copy.
        Sid      = "ReadCuratedGold"
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.curated.arn}/gold/*"
      },
      {
        # Athena writes query results on the caller's behalf, so the reader needs
        # to write the results prefix and read back what it wrote.
        Sid      = "ReadWriteResultsPrefix"
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject"]
        Resource = "${aws_s3_bucket.results.arn}/results/*"
      },
      {
        Sid      = "ResultsBucketLocation"
        Effect   = "Allow"
        Action   = ["s3:GetBucketLocation", "s3:ListBucket"]
        Resource = aws_s3_bucket.results.arn
        Condition = {
          StringLike = { "s3:prefix" = ["results/*"] }
        }
      },
      {
        # Read the one database and its tables. No CreateTable, UpdateTable or DeleteTable.
        # GetDatabases is deliberately omitted: it would list every database in the account.
        Sid    = "ReadGlueGoldDatabase"
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartition",
          "glue:GetPartitions",
        ]
        Resource = [
          "arn:aws:glue:${local.region}:${local.account_id}:catalog",
          "arn:aws:glue:${local.region}:${local.account_id}:database/${aws_glue_catalog_database.gold.name}",
          "arn:aws:glue:${local.region}:${local.account_id}:table/${aws_glue_catalog_database.gold.name}/*",
        ]
      },
      {
        # Run queries and read results on this workgroup only.
        Sid    = "QueryThisWorkgroupOnly"
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:StopQueryExecution",
          "athena:BatchGetQueryExecution",
          "athena:GetWorkGroup",
        ]
        Resource = [
          "arn:aws:athena:${local.region}:${local.account_id}:workgroup/${aws_athena_workgroup.analytics.name}",
        ]
      },
      {
        # Athena reads the default data catalog (Glue) to resolve table metadata.
        Sid      = "AthenaDefaultCatalog"
        Effect   = "Allow"
        Action   = ["athena:GetDataCatalog"]
        Resource = "arn:aws:athena:${local.region}:${local.account_id}:datacatalog/AwsDataCatalog"
      },
    ]
  })
}
