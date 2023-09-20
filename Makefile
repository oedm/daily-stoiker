.ONESHELL:
.SHELL := /usr/bin/bash
BOLD=$(shell tput bold)
RED=$(shell tput setaf 1)
GREEN=$(shell tput setaf 2)
YELLOW=$(shell tput setaf 3)
RESET=$(shell tput sgr0)

# Check for necessary tools
EXECUTABLES = aws docker-compose sam
K := $(foreach exec,$(EXECUTABLES),\
	$(if $(shell which $(exec)),some string,$(error "$(BOLD)$(RED)No $(exec) in PATH$(RESET)")))


.PHONY: 
start: build ## Start Lambda and API Gateway on localhost
	sam local start-api --env-vars db/env.json # or start-lambda

local-boot:
	docker-compose up -d

local-stop: ## Treminate DynamoDB local
	docker-compose down

pre-admin:
	@if [ -z `which dynamodb-admin 2> /dev/null` ]; then \
		echo "Need to install dynamodb-admin, execute \"npm install dynamodb-admin -g\"";\
		exit 1;\
	fi

dynamodb-admin: pre-admin ## Start DaynamoDB GUI
	DYNAMO_ENDPOINT=http://localhost:18000 dynamodb-admin

local-create-table: ## Creates local newsletter table
	aws dynamodb create-table --cli-input-json file://db/create_users_table.json --endpoint-url http://localhost:18000

local-start: local-boot local-create-table ## Start local development environment
	aws dynamodb batch-write-item --request-items file://db/development_data.json --endpoint-url http://localhost:18000

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

local-execute: ## Run lambda function locally
	environment=local python3 lambda/mailer/lambda_handler.py

validate:
	cdk synth

dev-diff:	## Compare cloudfront development stack
	cdk diff --profile moed daily-stoiker-dev

dev-deploy:	validate ## Rollout aws development stack
	cdk deploy --profile moed daily-stoiker-dev

prod-diff:	## Compare cloudfront production stack
	cdk diff --profile moed daily-stoiker-prod

prod-deploy: validate ## Rollout aws production stack
	cdk deploy --profile moed daily-stoiker-prod