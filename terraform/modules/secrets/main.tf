# Shell resources only — no secret values in Terraform state.
# Populate values out-of-band: aws secretsmanager put-secret-value --secret-id <name> --secret-string <value>

resource "aws_secretsmanager_secret" "db_password" {
  name                    = "/nexus/${var.environment}/db_password"
  recovery_window_in_days = var.recovery_window_in_days
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "/nexus/${var.environment}/jwt_secret"
  recovery_window_in_days = var.recovery_window_in_days
}

resource "aws_secretsmanager_secret" "redis_url" {
  name                    = "/nexus/${var.environment}/redis_url"
  recovery_window_in_days = var.recovery_window_in_days
}

resource "aws_secretsmanager_secret" "database_url" {
  name                    = "/nexus/${var.environment}/database_url"
  recovery_window_in_days = var.recovery_window_in_days
}

resource "aws_secretsmanager_secret" "linkedin_client_id" {
  name                    = "/nexus/${var.environment}/linkedin_client_id"
  recovery_window_in_days = var.recovery_window_in_days
}

resource "aws_secretsmanager_secret" "linkedin_client_secret" {
  name                    = "/nexus/${var.environment}/linkedin_client_secret"
  recovery_window_in_days = var.recovery_window_in_days
}

resource "aws_secretsmanager_secret" "openclaw_api_key" {
  name                    = "/nexus/${var.environment}/openclaw_api_key"
  recovery_window_in_days = var.recovery_window_in_days
}

resource "aws_secretsmanager_secret" "sendgrid_api_key" {
  name                    = "/nexus/${var.environment}/sendgrid_api_key"
  recovery_window_in_days = var.recovery_window_in_days
}
