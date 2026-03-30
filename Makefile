.PHONY: dev test lint format migrate seed docker-up docker-down tf-plan tf-apply tf-bootstrap tf-init-staging tf-init-prod tf-plan-staging tf-plan-prod tf-apply-staging tf-validate tf-secrets-staging tf-secrets-prod

dev:
	cd deploy && docker-compose up --build

test:
	docker-compose -f deploy/docker-compose.yml run --rm backend \
		pytest backend/tests/ -v --cov=backend --cov-report=html --cov-fail-under=85

lint:
	ruff check backend/
	mypy backend/ --ignore-missing-imports

format:
	ruff format backend/
	black backend/

migrate:
	docker-compose -f deploy/docker-compose.yml run --rm backend \
		alembic upgrade head

seed:
	docker-compose -f deploy/docker-compose.yml run --rm backend \
		python -m backend.seed_data

docker-up:
	docker-compose -f deploy/docker-compose.yml up -d

docker-down:
	docker-compose -f deploy/docker-compose.yml down -v

tf-plan:
	cd terraform && terraform plan -var-file=terraform.tfvars

tf-apply:
	cd terraform && terraform apply -var-file=terraform.tfvars -auto-approve

# --- Terraform ---
tf-bootstrap:
	cd terraform/bootstrap && terraform init && terraform apply -auto-approve
	@echo "State bucket created. Run 'make tf-init-staging' next."

tf-init-staging:
	cd terraform/environments/staging && terraform init

tf-init-prod:
	cd terraform/environments/prod && terraform init

tf-plan-staging:
	cd terraform/environments/staging && terraform plan

tf-plan-prod:
	cd terraform/environments/prod && terraform plan

tf-apply-staging:
	cd terraform/environments/staging && terraform apply

tf-validate:
	cd terraform/environments/staging && terraform validate
	cd terraform/environments/prod && terraform validate

tf-secrets-staging:
	aws secretsmanager put-secret-value --secret-id /nexus/staging/db_password --secret-string "$$(openssl rand -base64 32)"
	aws secretsmanager put-secret-value --secret-id /nexus/staging/jwt_secret --secret-string "$$(openssl rand -base64 48)"
	@echo "Populate remaining secrets (database_url, redis_url, etc.) after terraform apply provides endpoints."

tf-secrets-prod:
	aws secretsmanager put-secret-value --secret-id /nexus/prod/db_password --secret-string "$$(openssl rand -base64 32)"
	aws secretsmanager put-secret-value --secret-id /nexus/prod/jwt_secret --secret-string "$$(openssl rand -base64 48)"
	@echo "Populate remaining secrets (database_url, redis_url, etc.) after terraform apply provides endpoints."
