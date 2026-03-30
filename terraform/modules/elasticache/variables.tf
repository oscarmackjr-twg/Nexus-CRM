variable "app_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "redis_security_group_id" {
  type = string
}

variable "redis_node_type" {
  type = string
}

variable "num_cache_clusters" {
  type    = number
  default = 1
}
