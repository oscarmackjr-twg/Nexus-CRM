variable "app_name" {
  type    = string
  default = "nexus-crm"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "aws_region" {
  type    = string
  default = "ap-southeast-1"
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.large"
}

variable "db_storage_gb" {
  type    = number
  default = 50
}

variable "db_multi_az" {
  type    = bool
  default = true
}

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.medium"
}

variable "github_repository" {
  type        = string
  description = "GitHub repository in owner/name format for OIDC trust."
}

variable "nat_gateway_count" {
  type    = number
  default = 2
}

variable "create_oidc_provider" {
  type        = bool
  default     = false
  description = "Set to true for the first environment to provision the account-scoped GitHub OIDC provider. Set to false for subsequent environments."
}

# Phase 14 forward-compatibility placeholders
variable "app_domain" {
  type        = string
  default     = ""
  description = "Custom domain (e.g. crm.example.com). Leave empty for Phase 13 deployment."
}

variable "acm_certificate_arn" {
  type        = string
  default     = ""
  description = "ACM certificate ARN for the custom domain. Leave empty for Phase 13 deployment."
}
