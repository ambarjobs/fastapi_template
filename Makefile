SHELL=/bin/bash

include db.env
include app_db.env

ENVFILES = --env-file db.env --env-file test_db.env


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
start: ## Start containers. `recreate=true` parameter force containers recreation.
ifdef recreate
	@docker compose $(ENVFILES) up --force-recreate -d
else
	@docker compose $(ENVFILES) up -d
endif

# --------------------------------------------------------------------------------------------------
.PHONY: stop
stop: ## Stop containers.
	@docker compose $(ENVFILES) stop

# --------------------------------------------------------------------------------------------------
.PHONY: restart
restart: ## Restart all containers
	@docker compose $(ENVFILES) stop
	@sleep 2
	@docker compose $(ENVFILES) up -d

# --------------------------------------------------------------------------------------------------
.PHONY: build no_cache
build: --validate_env ## Build images and start the containers. `no_cache=true` parameter ignores cache.

	@docker compose $(ENVFILES) stop
ifdef no_cache
	@echo "Disregarding docker cache .."
	@docker compose $(ENVFILES) build --no-cache
else
	@docker compose $(ENVFILES) build
endif

# --------------------------------------------------------------------------------------------------
.PHONY: reset-containers remove_volumes
reset-containers: ## Remove build's containers and images.
ifdef remove_volumes:
	@docker compose $(ENVFILES) down --volumes
else
	@docker compose $(ENVFILES) down
endif
	@docker rmi fastapi_template-app fastapi_template-postgresql-db 2> /dev/null || echo "No images found."

# --------------------------------------------------------------------------------------------------
.PHONY: rebuild-containers remove_volumes
rebuild-containers: reset-containers remove_volumes ## Destroy and recreate all containers from last built images.
	@docker compose $(ENVFILES) build --no-cache
	@docker compose $(ENVFILES) up -d

# --------------------------------------------------------------------------------------------------
.PHONY: remove-all
remove-all: ## Remove all containers and wipe all data
	@docker compose $(ENVFILES) down --volumes


# ==================================================================================================
#  Information commands
# --------------------------------------------------------------------------------------------------
.PHONY: status
status: ## Show status of the containers.
	@docker compose $(ENVFILES) ps --format 'table {{.Name}}\t{{.Service}}\t{{.Status}}'

# --------------------------------------------------------------------------------------------------
.PHONY: logs service
logs: ## Show logs of the services. `logs=<service name>` indicates specific logs to show.
	@docker compose $(ENVFILES) logs -t -f ${service}

# ==================================================================================================
#  App commands
# --------------------------------------------------------------------------------------------------
.PHONY: app-status
app-status: ## Show status of the app container.
	@docker inspect template-app --format "{{.State.Status}}"

# --------------------------------------------------------------------------------------------------
.PHONY: inside
inside: ## Reach OS shell inside app container.
	@docker compose $(ENVFILES) exec -it app /bin/bash

# --------------------------------------------------------------------------------------------------
.PHONY: prep-dev
prep-dev: ## Prepare development environment inside app container.
	@docker compose $(ENVFILES) exec -it app /deploy/prep_dev

# --------------------------------------------------------------------------------------------------
.PHONY: shell
shell: ## Python shell inside app container.
	@docker compose $(ENVFILES) exec -it app /usr/local/bin/bpython || (echo "You need run make prep_dev first to be able to use this command." && exit 1)

# --------------------------------------------------------------------------------------------------
.PHONY: delete_bytecode
delete_bytecode: # Remove Python bytecode compiled files
	@docker compose $(ENVFILES) exec app find . -name "*.pyc" -delete
	@docker compose $(ENVFILES) exec app find . -name "__pycache__" -delete

# --------------------------------------------------------------------------------------------------
args =

.PHONY: test file class test_name module args
test: # Execute test suite, optionally restricted to a `file`, `class`, `test_name` or `module`.
ifdef module
	@docker compose $(ENVFILES) exec app pytest ${args} -k ${module}
else ifdef test_name
	@docker compose $(ENVFILES) exec app pytest ${args} tests/${file}::${class}::${test_name}
else ifdef class
	@docker compose $(ENVFILES) exec app pytest ${args} tests/${file}::${class}
else ifdef file
	@docker compose $(ENVFILES) exec app pytest ${args} tests/${file}
else
	@docker compose $(ENVFILES) exec app pytest ${args}
endif


# ==================================================================================================
#  PostgreSQL commands
# --------------------------------------------------------------------------------------------------
service = postgresql-db

.PHONY: inside-db service
inside-db: ## Reach OS shell inside PostgreSQL container. `service=<service name>` to choose which service.
	@docker compose $(ENVFILES) exec -it $(service) /bin/bash

# --------------------------------------------------------------------------------------------------
user = ${POSTGRES_USER}
database = ${APP_DATABASE}

.PHONY: db-cli service user database
db-cli: ## Database manager inside database container. Set `service=`, `user=` and `database=` accordingly.
	@docker compose $(ENVFILES) exec -it $(service) /bin/bash -c 'psql -U $(user) -d $(database)'


# ==================================================================================================
#  Tooling commands
# --------------------------------------------------------------------------------------------------
.PHONY: gen-requirements
gen-requirements: ## Generate requirements.txt from pyproject.toml configuration.
	@uv pip compile --all-extras pyproject.toml -o src/requirements.txt



.DEFAULT_GOAL := help
