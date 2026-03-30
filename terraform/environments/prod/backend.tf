terraform {
  backend "s3" {
    bucket       = "nexus-crm-terraform-state"
    key          = "prod/terraform.tfstate"
    region       = "ap-southeast-1"
    encrypt      = true
    use_lockfile = true
  }
}
