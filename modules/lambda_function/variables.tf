variable "function_name" { type = string }
variable "source_dir" { type = string }
variable "handler" {
  type    = string
  default = "lambda_function.lambda_handler"
}
variable "timeout" {
  type    = number
  default = 30
}
variable "memory_size" {
  type    = number
  default = 256
}
variable "environment_variables" {
  type    = map(string)
  default = {}
}
variable "policy_json" { type = string }
variable "tags" {
  type    = map(string)
  default = {}
}

