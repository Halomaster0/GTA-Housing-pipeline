variable "aws_region" {
  description = "Region for every resource. The new AWS experience fixes the project Region; this must match it (confirmed us-east-2 on 2026-11-04)."
  type        = string
  default     = "us-east-2"
}

variable "aws_profile" {
  description = "Named AWS CLI profile (SSO or assumed role). Credentials are never stored in this repo."
  type        = string
  default     = "gta-housing"
}

variable "alert_email" {
  description = "Address that receives budget alerts. Set in a gitignored *.tfvars file, never committed."
  type        = string

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+$", var.alert_email))
    error_message = "alert_email must look like an email address."
  }
}

variable "budget_limit_usd" {
  description = "Monthly gross-spend budget in USD. Credits are excluded, so this tracks real usage."
  type        = number
  default     = 5

  validation {
    condition     = var.budget_limit_usd > 0 && var.budget_limit_usd <= 50
    error_message = "budget_limit_usd must be between 0 and 50."
  }
}

variable "deployer_role_arn" {
  description = "IAM role ARN allowed to assume the Athena reader role (your SSO or deployer role). Set in a gitignored *.tfvars file."
  type        = string

  validation {
    condition     = can(regex("^arn:aws:iam::[0-9]{12}:role/", var.deployer_role_arn))
    error_message = "deployer_role_arn must be an IAM role ARN."
  }
}

variable "name_prefix" {
  description = "Prefix for resource names."
  type        = string
  default     = "gta-housing"
}

variable "scan_cutoff_bytes" {
  description = "Per-query data-scanned cutoff enforced by the Athena workgroup. Largest gold table is about 13 MB as Parquet, so 100 MiB is well above a full scan and far below anything costly. Athena's minimum is 10 MiB."
  type        = number
  default     = 104857600

  validation {
    condition     = var.scan_cutoff_bytes >= 10485760
    error_message = "scan_cutoff_bytes must be at least 10 MiB (10485760), Athena's minimum."
  }
}

variable "tables" {
  description = "Gold tables and their Glue column lists. Generated from the exported Parquet schemas by scripts/aws/gen_glue_schema.py into tables.auto.tfvars.json; do not edit by hand."
  type = map(object({
    columns = list(object({
      name = string
      type = string
    }))
  }))
  default = {}
}
