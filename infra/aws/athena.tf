# Athena workgroup. Enforced configuration means a query cannot override the results
# location or the scan cutoff. The cutoff is the cost guardrail: a query that would
# scan more than the limit is cancelled instead of billed.

resource "aws_athena_workgroup" "analytics" {
  name          = "${var.name_prefix}-analytics"
  force_destroy = true # lets destroy remove the workgroup even with query history

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = false
    bytes_scanned_cutoff_per_query     = var.scan_cutoff_bytes

    result_configuration {
      output_location = "s3://${aws_s3_bucket.results.bucket}/results/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }
}
