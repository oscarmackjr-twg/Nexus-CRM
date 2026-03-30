resource "random_password" "db" {
  length  = 32
  special = false
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.app_name}-${var.environment}-db-subnets"
  subnet_ids = var.private_subnet_ids
}

resource "aws_db_parameter_group" "this" {
  name   = "${var.app_name}-${var.environment}-pg17"
  family = "postgres17"

  parameter {
    name         = "rds.logical_replication"
    value        = "1"
    apply_method = "pending-reboot"
  }

  parameter {
    name         = "idle_in_transaction_session_timeout"
    value        = "30000"
    apply_method = "immediate"
  }

  parameter {
    name         = "wal_sender_timeout"
    value        = "0"
    apply_method = "immediate"
  }
}

resource "aws_db_instance" "this" {
  identifier                   = "${var.app_name}-${var.environment}-db"
  engine                       = "postgres"
  engine_version               = "17"
  instance_class               = var.db_instance_class
  allocated_storage            = var.db_storage_gb
  max_allocated_storage        = var.db_storage_gb * 2
  db_name                      = "nexuscrm"
  username                     = "nexuscrm"
  password                     = random_password.db.result
  db_subnet_group_name         = aws_db_subnet_group.this.name
  parameter_group_name         = aws_db_parameter_group.this.name
  vpc_security_group_ids       = [var.rds_security_group_id]
  multi_az                     = var.db_multi_az
  backup_retention_period      = 7
  deletion_protection          = var.enable_deletion_protection
  storage_encrypted            = true
  performance_insights_enabled = true
  auto_minor_version_upgrade   = true
  publicly_accessible          = false
  skip_final_snapshot          = !var.enable_deletion_protection
  final_snapshot_identifier    = var.enable_deletion_protection ? "${var.app_name}-${var.environment}-db-final" : null
  copy_tags_to_snapshot        = true
  apply_immediately            = false
  maintenance_window           = "sun:05:00-sun:06:00"
  backup_window                = "03:00-04:00"
}
