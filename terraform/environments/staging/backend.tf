terraform {
  backend "s3" {
    bucket       = "nexus-crm-terraform-state"
    key          = "staging/terraform.tfstate"
    region       = "ap-southeast-1"
    encrypt      = true
    use_lockfile = true
  }
}
