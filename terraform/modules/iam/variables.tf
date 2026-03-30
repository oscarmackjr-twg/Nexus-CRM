variable "app_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "github_repository" {
  type = string
}

variable "create_oidc_provider" {
  type        = bool
  default     = true
  description = "Whether to create the OIDC provider (account-scoped, only create once)"
}

variable "assets_bucket_arn" {
  type        = string
  default     = ""
  description = "S3 assets bucket ARN (Phase 14 — empty until then)"
}

variable "frontend_bucket_arn" {
  type        = string
  default     = ""
  description = "S3 frontend bucket ARN (Phase 14 — empty until then)"
}
