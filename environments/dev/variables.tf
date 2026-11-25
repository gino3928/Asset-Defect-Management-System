variable "aws_region" {
  description = "Deployment region for all application resources."
  type        = string
  default     = "us-east-2"

  validation {
    condition     = var.aws_region == "us-east-2"
    error_message = "This initial environment is intentionally pinned to us-east-2."
  }
}

variable "project_name" {
  description = "Prefix used for AWS resource names."
  type        = string
  default     = "asset-defect"
}

variable "environment" {
  description = "Deployment environment label."
  type        = string
  default     = "dev"
}

variable "slack_workspace_id" {
  description = "Expected Slack team/workspace ID; requests from another workspace are rejected."
  type        = string
}

variable "asset_agentcore_harness_arn" {
  description = "Optional Asset AgentCore harness ARN added in the next phase."
  type        = string
  default     = ""
}

variable "defect_agentcore_model_id" {
  description = "Bedrock foundation model used by the isolated defect review harness."
  type        = string
  default     = "amazon.nova-lite-v1:0"
}

variable "defect_agentcore_required" {
  description = "Fail the defect request if AgentCore is unavailable or returns an invalid review."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags merged into the standard tag set."
  type        = map(string)
  default     = {}
}
