data "aws_caller_identity" "current" {}

resource "aws_iam_openid_connect_provider" "github" {
  count           = var.create_oidc_provider ? 1 : 0
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

data "aws_iam_openid_connect_provider" "github" {
  count = var.create_oidc_provider ? 0 : 1
  url   = "https://token.actions.githubusercontent.com"
}

locals {
  name_prefix        = "${var.app_name}-${var.environment}"
  oidc_provider_arn  = var.create_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : data.aws_iam_openid_connect_provider.github[0].arn
  secret_arn_pattern = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:/nexus/${var.environment}/*"
}

resource "aws_iam_role" "execution" {
  name = "${local.name_prefix}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "execution_managed" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "execution_secrets" {
  name = "${local.name_prefix}-execution-secrets"
  role = aws_iam_role.execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = local.secret_arn_pattern
      }
    ]
  })
}

resource "aws_iam_role" "task" {
  name = "${local.name_prefix}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "task" {
  name = "${local.name_prefix}-task-policy"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      [
        {
          Effect   = "Allow"
          Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
          Resource = "*"
        }
      ],
      var.assets_bucket_arn != "" ? [
        {
          Effect   = "Allow"
          Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
          Resource = ["${var.assets_bucket_arn}/*"]
        },
        {
          Effect   = "Allow"
          Action   = ["s3:ListBucket"]
          Resource = [var.assets_bucket_arn]
        }
      ] : []
    )
  })
}

resource "aws_iam_role" "github_actions" {
  name = "${local.name_prefix}-github-actions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = local.oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repository}:*"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "github_actions" {
  name = "${local.name_prefix}-github-actions-policy"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      [
        {
          Effect   = "Allow"
          Action   = ["ecr:GetAuthorizationToken"]
          Resource = "*"
        },
        {
          Effect = "Allow"
          Action = [
            "ecr:BatchCheckLayerAvailability",
            "ecr:InitiateLayerUpload",
            "ecr:UploadLayerPart",
            "ecr:CompleteLayerUpload",
            "ecr:PutImage",
            "ecr:BatchGetImage"
          ]
          Resource = "arn:aws:ecr:${var.aws_region}:${data.aws_caller_identity.current.account_id}:repository/${var.app_name}-${var.environment}-*"
        },
        {
          Effect = "Allow"
          Action = [
            "ecs:DescribeServices",
            "ecs:UpdateService",
            "ecs:RegisterTaskDefinition",
            "ecs:DescribeTaskDefinition",
            "ecs:RunTask",
            "ecs:DescribeTasks",
            "ecs:StopTask"
          ]
          Resource = "*"
        },
        {
          Effect = "Allow"
          Action = ["iam:PassRole"]
          Resource = [
            aws_iam_role.execution.arn,
            aws_iam_role.task.arn
          ]
        },
        {
          Effect   = "Allow"
          Action   = ["secretsmanager:GetSecretValue"]
          Resource = local.secret_arn_pattern
        }
      ],
      var.frontend_bucket_arn != "" ? [
        {
          Effect = "Allow"
          Action = ["s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
          Resource = [
            var.frontend_bucket_arn,
            "${var.frontend_bucket_arn}/*"
          ]
        },
        {
          Effect   = "Allow"
          Action   = ["cloudfront:CreateInvalidation"]
          Resource = "*"
        }
      ] : []
    )
  })
}
