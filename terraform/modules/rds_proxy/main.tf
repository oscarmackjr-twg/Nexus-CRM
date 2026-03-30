locals {
  name_prefix = "${var.app_name}-${var.environment}"
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

resource "aws_iam_role" "rds_proxy" {
  name = "${local.name_prefix}-rds-proxy-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "rds.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "rds_proxy_secrets" {
  name = "${local.name_prefix}-rds-proxy-secrets"
  role = aws_iam_role.rds_proxy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = var.db_password_secret_arn
      }
    ]
  })
}

resource "aws_db_proxy" "this" {
  name                   = "${local.name_prefix}-proxy"
  debug_logging          = false
  engine_family          = "POSTGRESQL"
  idle_client_timeout    = 1800
  require_tls            = true
  role_arn               = aws_iam_role.rds_proxy.arn
  vpc_security_group_ids = [var.rds_proxy_security_group_id]
  vpc_subnet_ids         = var.private_subnet_ids

  auth {
    auth_scheme = "SECRETS"
    # Intentional: using password auth via Secrets Manager (not IAM database auth).
    # RDS Proxy reads the DB password from the Secrets Manager secret ARN.
    # The IAM role above (rds_proxy) grants the Proxy access to Secrets Manager.
    iam_auth   = "DISABLED"
    secret_arn = var.db_password_secret_arn
  }
}

resource "aws_db_proxy_default_target_group" "this" {
  db_proxy_name = aws_db_proxy.this.name

  connection_pool_config {
    max_connections_percent      = 100
    max_idle_connections_percent = 50
    connection_borrow_timeout    = 120
  }
}

resource "aws_db_proxy_target" "this" {
  db_instance_identifier = var.db_instance_identifier
  db_proxy_name          = aws_db_proxy.this.name
  target_group_name      = aws_db_proxy_default_target_group.this.name
}
