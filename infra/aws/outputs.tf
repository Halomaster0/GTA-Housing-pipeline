output "curated_bucket" {
  description = "Bucket holding gold Parquet under gold/<table>/."
  value       = aws_s3_bucket.curated.bucket
}

output "results_bucket" {
  description = "Bucket that receives Athena query results."
  value       = aws_s3_bucket.results.bucket
}

output "glue_database" {
  description = "Glue catalog database holding the gold tables."
  value       = aws_glue_catalog_database.gold.name
}

output "athena_workgroup" {
  description = "Athena workgroup with enforced configuration and the scan cutoff."
  value       = aws_athena_workgroup.analytics.name
}

output "athena_reader_role_arn" {
  description = "Role the parity test assumes. Do not commit the value."
  value       = aws_iam_role.athena_reader.arn
}
