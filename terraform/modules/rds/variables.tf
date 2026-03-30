variable "app_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "rds_security_group_id" {
  type = string
}

variable "db_instance_class" {
  type = string
}

variable "db_storage_gb" {
  type = number
}

variable "db_multi_az" {
  type = bool
}

variable "enable_deletion_protection" {
  type = bool
}
