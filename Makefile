DOCKER_COMPOSE_DEV = docker-compose
DOCKER_COMPOSE_CI = docker-compose -f docker-compose.yml
DOCKER_COMPOSE = $(DOCKER_COMPOSE_DEV)

VENV = venv

ifeq ($(OS),Windows_NT)
	VENV_BIN = $(VENV)/Scripts
else
	VENV_BIN = $(VENV)/bin
endif

PYTHON = $(VENV_BIN)/python
PIP = $(VENV_BIN)/python -m pip

SYSTEM_PYTHON = python3

ARGS =

SCIENCEBEAM_PARSER_PORT = 8080

PDFALTO_CONVERT_API_URL = http://localhost:$(SCIENCEBEAM_PARSER_PORT)/api/pdfalto
EXAMPLE_PDF_DOCUMENT = test-data/minimal-example.pdf


SCIENCEBEAM_DELFT_MAX_SEQUENCE_LENGTH = 2000
SCIENCEBEAM_DELFT_INPUT_WINDOW_STRIDE = 1800
SCIENCEBEAM_DELFT_BATCH_SIZE = 1
SCIENCEBEAM_DELFT_STATEFUL = false


DOCKER_PDFALTO_CONVERT_API_URL = http://sciencebeam-parser:8070/api/pdfalto
DOCKER_DEV_RUN = $(DOCKER_COMPOSE) run --rm sciencebeam-parser-dev
DOCKER_DEV_PYTHON = $(DOCKER_DEV_RUN) python


venv-clean:
	@if [ -d "$(VENV)" ]; then \
		rm -rf "$(VENV)"; \
	fi


venv-create:
	$(SYSTEM_PYTHON) -m venv $(VENV)


dev-install:
	$(PIP) install -r requirements.build.txt
	$(PIP) install -r requirements.cpu.txt
	$(PIP) install -r requirements.dev.txt
	$(PIP) install -r requirements.delft.txt --no-deps
	$(PIP) install -r requirements.txt


dev-venv: venv-create dev-install


dev-flake8:
	$(PYTHON) -m flake8 sciencebeam_parser tests setup.py


dev-pylint:
	$(PYTHON) -m pylint sciencebeam_parser tests setup.py


dev-mypy:
	$(PYTHON) -m mypy --ignore-missing-imports sciencebeam_parser tests setup.py


dev-lint: dev-flake8 dev-pylint dev-mypy


dev-pytest:
	$(PYTHON) -m pytest -p no:cacheprovider $(ARGS)


dev-watch:
	$(PYTHON) -m pytest_watch -- -p no:cacheprovider -p no:warnings $(ARGS)


dev-test: dev-lint dev-pytest


dev-start:
	SCIENCEBEAM_DELFT_MAX_SEQUENCE_LENGTH=$(SCIENCEBEAM_DELFT_MAX_SEQUENCE_LENGTH) \
	SCIENCEBEAM_DELFT_INPUT_WINDOW_STRIDE=$(SCIENCEBEAM_DELFT_INPUT_WINDOW_STRIDE) \
	SCIENCEBEAM_DELFT_BATCH_SIZE=$(SCIENCEBEAM_DELFT_BATCH_SIZE) \
	SCIENCEBEAM_DELFT_STATEFUL=$(SCIENCEBEAM_DELFT_STATEFUL) \
		$(PYTHON) -m sciencebeam_parser.service.server --port=$(SCIENCEBEAM_PARSER_PORT)


dev-start-debug:
	FLASK_ENV=development \
	SCIENCEBEAM_PARSER__LOGGING__HANDLERS__LOG_FILE__LEVEL=DEBUG \
	$(MAKE) dev-start


dev-start-no-debug-logging-auto-reload:
	FLASK_ENV=development \
	FLASK_DEBUG=1 \
	SCIENCEBEAM_PARSER__LOGGING__HANDLERS__LOG_FILE__LEVEL=INFO \
	$(MAKE) dev-start


dev-end-to-end:
	curl --fail --show-error \
		--form "file=@$(EXAMPLE_PDF_DOCUMENT);filename=$(EXAMPLE_PDF_DOCUMENT)" \
		--silent "$(PDFALTO_CONVERT_API_URL)" \
		> /dev/null


run:
	$(PYTHON) -m sciencebeam_parser $(ARGS)


docker-build-all:
	$(DOCKER_COMPOSE) build


docker-lint:
	$(MAKE) PYTHON="$(DOCKER_DEV_PYTHON)" dev-lint


docker-pytest:
	$(MAKE) PYTHON="$(DOCKER_DEV_PYTHON)" dev-pytest


docker-wait-for-api:
	$(DOCKER_COMPOSE) run --rm wait-for-it \
		"sciencebeam-parser:8070" \
		--timeout=30 \
		--strict \
		-- echo "ScienceBeam Parser API is up"


docker-start:
	$(DOCKER_COMPOSE) up -d


docker-stop:
	$(DOCKER_COMPOSE) down


docker-start-and-wait-for-api:
	$(MAKE) docker-start
	$(MAKE) docker-wait-for-api


docker-end-to-end: docker-start-and-wait-for-api
	$(DOCKER_DEV_RUN) curl --fail --show-error \
		--form "file=@$(EXAMPLE_PDF_DOCUMENT);filename=$(EXAMPLE_PDF_DOCUMENT)" \
		--silent "$(DOCKER_PDFALTO_CONVERT_API_URL)" \
		--output /dev/null


ci-build-all:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" docker-build-all


ci-lint:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" docker-lint


ci-pytest:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" docker-pytest


ci-end-to-end:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" docker-end-to-end


ci-clean:
	$(DOCKER_COMPOSE_CI) down -v
