# Storage: one curated bucket for gold Parquet and one bucket for Athena results.
# Both: public access fully blocked, default encryption (SSE-S3), object ownership
# enforced (ACLs disabled). force_destroy lets `terraform destroy` empty them; the
# data is reproducible from DuckDB, so nothing is lost.

resource "random_id" "suffix" {
  byte_length = 4 # 8 hex characters. Keeps bucket names unique without the account ID.
}

locals {
  curated_bucket = "${var.name_prefix}-curated-${random_id.suffix.hex}"
  results_bucket = "${var.name_prefix}-athena-results-${random_id.suffix.hex}"
}

resource "aws_s3_bucket" "curated" {
  bucket        = local.curated_bucket
  force_destroy = true
}

resource "aws_s3_bucket" "results" {
  bucket        = local.results_bucket
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "curated" {
  bucket                  = aws_s3_bucket.curated.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "results" {
  bucket                  = aws_s3_bucket.results.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "curated" {
  bucket = aws_s3_bucket.curated.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_ownership_controls" "results" {
  bucket = aws_s3_bucket.results.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "curated" {
  bucket = aws_s3_bucket.curated.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "results" {
  bucket = aws_s3_bucket.results.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "results" {
  bucket = aws_s3_bucket.results.id

  rule {
    id     = "expire-query-results"
    status = "Enabled"

    filter {
      prefix = "results/"
    }

    expiration {
      days = 3
    }
  }
}
