provider "aws" {
  # Keep the state bucket beside the application unless a later DR design says otherwise.
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

