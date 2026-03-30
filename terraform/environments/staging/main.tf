terraform {
  required_version = ">= 1.10, < 2.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.app_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

locals {
  name_prefix   = "${var.app_name}-${var.environment}"
  is_production = var.environment == "prod"
}

# --- ECR Repositories (inline, not in a module) ---
# Only api and worker repos — frontend is served from S3+CloudFront (no container). Per INFRA-04.

resource "aws_ecr_repository" "api" {
  name                 = "${local.name_prefix}-api"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "worker" {
  name                 = "${local.name_prefix}-worker"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

resource "aws_ecr_lifecycle_policy" "worker" {
  repository = aws_ecr_repository.worker.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

# --- Modules ---

module "networking" {
  source            = "../../modules/networking"
  app_name          = var.app_name
  environment       = var.environment
  nat_gateway_count = var.nat_gateway_count
}

module "rds" {
  source                     = "../../modules/rds"
  app_name                   = var.app_name
  environment                = var.environment
  private_subnet_ids         = module.networking.private_subnet_ids
  rds_security_group_id      = module.networking.rds_security_group_id
  db_instance_class          = var.db_instance_class
  db_storage_gb              = var.db_storage_gb
  db_multi_az                = var.db_multi_az
  enable_deletion_protection = local.is_production
}

module "rds_proxy" {
  source                      = "../../modules/rds_proxy"
  app_name                    = var.app_name
  environment                 = var.environment
  private_subnet_ids          = module.networking.private_subnet_ids
  rds_proxy_security_group_id = module.networking.rds_proxy_security_group_id
  db_instance_identifier      = module.rds.db_instance_identifier
  db_password_secret_arn      = module.secrets.db_password_secret_arn
}

module "elasticache" {
  source                  = "../../modules/elasticache"
  app_name                = var.app_name
  environment             = var.environment
  private_subnet_ids      = module.networking.private_subnet_ids
  redis_security_group_id = module.networking.redis_security_group_id
  redis_node_type         = var.redis_node_type
}

module "secrets" {
  source      = "../../modules/secrets"
  app_name    = var.app_name
  environment = var.environment
}

module "iam" {
  source               = "../../modules/iam"
  app_name             = var.app_name
  environment          = var.environment
  aws_region           = var.aws_region
  github_repository    = var.github_repository
  create_oidc_provider = var.create_oidc_provider
}
