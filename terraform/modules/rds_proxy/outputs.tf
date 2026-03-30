output "proxy_endpoint" {
  description = "RDS Proxy endpoint (use instead of RDS endpoint)"
  value       = aws_db_proxy.this.endpoint
}

output "proxy_arn" {
  value = aws_db_proxy.this.arn
}
