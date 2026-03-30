resource "aws_elasticache_subnet_group" "this" {
  name       = "${var.app_name}-${var.environment}-redis-subnets"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_replication_group" "this" {
  replication_group_id = "${var.app_name}-${var.environment}-redis"
  description          = "Redis replication group for ${var.app_name} ${var.environment}"

  node_type          = var.redis_node_type
  num_cache_clusters = var.num_cache_clusters
  port               = 6379
  subnet_group_name  = aws_elasticache_subnet_group.this.name
  security_group_ids = [var.redis_security_group_id]

  engine_version       = "7.1"
  parameter_group_name = "default.redis7"

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  transit_encryption_mode    = "required"

  automatic_failover_enabled = var.num_cache_clusters >= 2
  multi_az_enabled           = var.num_cache_clusters >= 2

  apply_immediately = false

  lifecycle {
    ignore_changes = [num_cache_clusters]
  }
}
