variable "aws_region" {
  description = "AWS region that stores Terraform state."
  type        = string
  default     = "us-east-2"
}

variable "project_name" {
  description = "Short project name used in the globally unique bucket name."
  type        = string
  default     = "asset-defect-management"
}

variable "tags" {
  description = "Tags applied to bootstrap resources."
  type        = map(string)
  default = {
    Project   = "asset-defect-management"
    ManagedBy = "Terraform"
  }
}

