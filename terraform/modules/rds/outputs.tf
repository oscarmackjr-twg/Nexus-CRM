output "endpoint" {
  value = aws_db_instance.this.address
}

output "port" {
  value = aws_db_instance.this.port
}

output "username" {
  value = aws_db_instance.this.username
}

output "password" {
  value     = random_password.db.result
  sensitive = true
}

output "database_name" {
  value = aws_db_instance.this.db_name
}

output "db_instance_identifier" {
  value = aws_db_instance.this.identifier
}
