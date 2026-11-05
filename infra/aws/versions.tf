# Pinned Terraform and provider versions. Exact pins keep plans reproducible.
# `.terraform.lock.hcl` (committed) pins the provider build hashes.
terraform {
  required_version = "= 1.16.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  default_tags {
    tags = {
      project    = "gta-housing"
      managed_by = "terraform"
    }
  }
}
