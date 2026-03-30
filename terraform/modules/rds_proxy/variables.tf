variable "app_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "rds_proxy_security_group_id" {
  type = string
}

variable "db_instance_identifier" {
  type = string
}

variable "db_password_secret_arn" {
  type        = string
  description = "ARN of the Secrets Manager secret containing the DB password"
}
