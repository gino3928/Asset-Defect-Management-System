terraform {
  required_version = ">= 1.15.0, < 2.0.0"

  # The bucket is supplied with -backend-config so no account-specific value is committed.
  backend "s3" {
    key          = "asset-defect-management/dev/terraform.tfstate"
    region       = "us-east-2"
    encrypt      = true
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.55"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.7"
    }
  }
}

