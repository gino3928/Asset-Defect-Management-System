variable "name" { type = string }
variable "hash_key" { type = string }
variable "ttl_attribute" {
  type    = string
  default = null
}
variable "point_in_time_recovery" {
  type    = bool
  default = true
}
variable "tags" {
  type    = map(string)
  default = {}
}

