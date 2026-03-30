variable "app_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "nat_gateway_count" {
  type    = number
  default = 2
}
