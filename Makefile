SHELL=/bin/bash

include .env


all:
	@echo "Try 'make help'"

# --------------------------------------------------------------------------------------------------
.PHONY: help
help: ## Makefile help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# --------------------------------------------------------------------------------------------------
.PHONY: --validate_env
--validate_env: ## Validate docker environment requirements.
	@command -v docker > /dev/null || (echo "You need to install docker before proceeding" && exit 1)
	@command -v docker compose > /dev/null || (echo "You need to install docker compose before proceeding" && exit 1)


# ==================================================================================================
#  Docker commands
# --------------------------------------------------------------------------------------------------
.PHONY: start recreate
start: ## Start containers.
ifdef recreate
	@docker compose up --force-recreate -d
else
	@docker compose up -d
endif

# --------------------------------------------------------------------------------------------------
.PHONY: stop
stop: ## Stop containers.
	@docker compose stop

# --------------------------------------------------------------------------------------------------
.PHONY: restart
restart: ## Restart all containers
	@docker compose stop
	@sleep 2
	@docker compose up -d

# --------------------------------------------------------------------------------------------------
.PHONY: build no_cache
build: --validate_env ## Build images and start the containers.

	@docker compose stop
ifdef no_cache
	@echo "Disregarding docker cache .."
	@docker compose build --no-cache
else
	@docker compose build
endif

# --------------------------------------------------------------------------------------------------
.PHONY: reset-containers remove_volumes
reset-containers: ## Remove build's containers and images.
ifdef remove_volumes:
	@docker compose down --volumes
else
	@docker compose down
endif
	@docker rmi fastapi_template-app fastapi_template-postgresql-db 2> /dev/null || echo "No images found."

# --------------------------------------------------------------------------------------------------
.PHONY: rebuild-containers remove_volumes
rebuild-containers: reset-containers remove_volumes ## Destroy and recreate all containers from last built images.
	@docker compose build --no-cache
	@docker compose up -d

# --------------------------------------------------------------------------------------------------
.PHONY: remove-all
remove-all: ## Remove all containers and wipe all data
	@docker compose down --volumes


# ==================================================================================================
#  Information commands
# --------------------------------------------------------------------------------------------------
.PHONY: status
status: ## Show status of the containers.
	@docker compose ps --format 'table {{.Name}}\t{{.Service}}\t{{.Status}}'

# --------------------------------------------------------------------------------------------------
.PHONY: logs service
logs: ## Show status of the containers.
	@docker compose logs -t -f ${service}

# ==================================================================================================
#  App commands
# --------------------------------------------------------------------------------------------------
.PHONY: app-status
app-status: ## Show status of the app container.
	@docker inspect template-app --format "{{.State.Status}}"

# --------------------------------------------------------------------------------------------------
.PHONY: inside
inside: ## Reach OS shell inside app container.
	@docker compose exec -it app /bin/bash

# --------------------------------------------------------------------------------------------------
.PHONY: prep-dev
prep-dev: ## Prepare development environment inside app container.
	@docker compose exec -it app /deploy/prep_dev

# --------------------------------------------------------------------------------------------------
.PHONY: shell
shell: ## Python shell inside app container.
	@docker compose exec -it app /usr/local/bin/bpython || (echo "You need run make prep_dev first to be able to use this command." && exit 1)

# --------------------------------------------------------------------------------------------------
.PHONY: delete_bytecode
delete_bytecode: # Remove Python bytecode compiled files
	@docker compose exec app find . -name "*.pyc" -delete
	@docker compose exec app find . -name "__pycache__" -delete

# --------------------------------------------------------------------------------------------------
.PHONY: test file class test_name module
test: # Execute test suite, optionally restricted to a `file`, `class`, `test_name` or `module`.
ifdef module
	@docker compose exec app pytest -k ${module}
else ifdef test_name
	@docker compose exec app pytest tests/${file}::${class}::${test_name}
else ifdef class
	@docker compose exec app pytest tests/${file}::${class}
else ifdef file
	@docker compose exec app pytest tests/${file}
else
	@docker compose exec app pytest
endif


# ==================================================================================================
#  PostgreSQL commands
# --------------------------------------------------------------------------------------------------
.PHONY: inside-db
inside-db: ## Reach OS shell inside PostgreSQL container.
	@docker compose exec -it postgresql-db /bin/bash

# --------------------------------------------------------------------------------------------------
user = ${POSTGRES_USER}
database = template_db

.PHONY: db-cli user database
db-cli: ## Database manager inside database container.
	@docker compose exec -it postgresql-db /bin/bash -c 'psql -U $(user) -d $(database)'


# ==================================================================================================
#  Tooling commands
# --------------------------------------------------------------------------------------------------
.PHONY: gen-requirements
gen-requirements: ## Generate requirements.txt from pyproject.toml configuration.
	@uv pip compile pyproject.toml -o src/requirements.txt



.DEFAULT_GOAL := help
