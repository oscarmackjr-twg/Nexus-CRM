output "secret_arns" {
  description = "Map of all secret ARNs"
  value = {
    db_password            = aws_secretsmanager_secret.db_password.arn
    jwt_secret             = aws_secretsmanager_secret.jwt_secret.arn
    redis_url              = aws_secretsmanager_secret.redis_url.arn
    database_url           = aws_secretsmanager_secret.database_url.arn
    linkedin_client_id     = aws_secretsmanager_secret.linkedin_client_id.arn
    linkedin_client_secret = aws_secretsmanager_secret.linkedin_client_secret.arn
    openclaw_api_key       = aws_secretsmanager_secret.openclaw_api_key.arn
    sendgrid_api_key       = aws_secretsmanager_secret.sendgrid_api_key.arn
  }
}

output "db_password_secret_arn" {
  description = "ARN of db_password secret (used by RDS Proxy)"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "jwt_secret_arn" {
  description = "ARN of jwt_secret"
  value       = aws_secretsmanager_secret.jwt_secret.arn
}

output "redis_url_secret_arn" {
  description = "ARN of redis_url secret"
  value       = aws_secretsmanager_secret.redis_url.arn
}

output "database_url_secret_arn" {
  description = "ARN of database_url secret"
  value       = aws_secretsmanager_secret.database_url.arn
}
