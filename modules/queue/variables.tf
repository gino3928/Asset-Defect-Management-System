variable "name" {
  description = "Base name for the workload queue."
  type        = string
}

variable "visibility_timeout_seconds" {
  description = "Time allowed for one Lambda processing attempt."
  type        = number
  default     = 180
}

variable "max_receive_count" {
  description = "Failed receives before a message moves to the DLQ."
  type        = number
  default     = 3
}

variable "tags" {
  description = "Tags applied to both queues."
  type        = map(string)
  default     = {}
}

