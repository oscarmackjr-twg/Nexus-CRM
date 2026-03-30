# --- Phase 13 outputs (consumed by Phase 14 and Phase 15) ---

# Networking
output "vpc_id" {
  value = module.networking.vpc_id
}

output "public_subnet_ids" {
  value = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  value = module.networking.private_subnet_ids
}

output "alb_security_group_id" {
  value = module.networking.alb_security_group_id
}

output "api_security_group_id" {
  value = module.networking.api_security_group_id
}

output "worker_security_group_id" {
  value = module.networking.worker_security_group_id
}

# RDS
output "rds_endpoint" {
  value = module.rds.endpoint
}

output "rds_proxy_endpoint" {
  value = module.rds_proxy.proxy_endpoint
}

# ElastiCache
output "redis_endpoint" {
  value = module.elasticache.endpoint
}

# ECR
output "api_ecr_repository_url" {
  value = aws_ecr_repository.api.repository_url
}

output "worker_ecr_repository_url" {
  value = aws_ecr_repository.worker.repository_url
}

# Secrets
output "secret_arns" {
  value = module.secrets.secret_arns
}

# IAM
output "execution_role_arn" {
  value = module.iam.execution_role_arn
}

output "task_role_arn" {
  value = module.iam.task_role_arn
}

output "github_actions_role_arn" {
  value = module.iam.github_actions_role_arn
}
