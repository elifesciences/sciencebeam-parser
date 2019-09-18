DOCKER_COMPOSE_DEV = docker-compose
DOCKER_COMPOSE_CI = docker-compose -f docker-compose.yml
DOCKER_COMPOSE = $(DOCKER_COMPOSE_DEV)

VENV = venv
PIP = $(VENV)/bin/pip
PYTHON = $(VENV)/bin/python

RUN_DEV = $(DOCKER_COMPOSE) run --rm sciencebeam-dev

NO_BUILD =
ARGS =


.PHONY: logs


venv-clean:
	@if [ -d "$(VENV)" ]; then \
		rm -rf "$(VENV)"; \
	fi


venv-create:
	python3 -m venv $(VENV)


dev-install:
	$(PIP) install -r requirements.prereq.txt
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements.dev.txt
	$(PIP) install -e . --no-deps


dev-venv: venv-create dev-install


dev-flake8:
	$(PYTHON) -m flake8 sciencebeam tests setup.py


dev-pylint:
	$(PYTHON) -m pylint sciencebeam tests setup.py


dev-lint: dev-flake8 dev-pylint


dev-pytest:
	$(PYTHON) -m pytest -p no:cacheprovider $(ARGS)


dev-watch:
	$(PYTHON) -m pytest_watch --verbose --ext=.py,.xsl -- -p no:cacheprovider -k 'not slow' $(ARGS)


dev-watch-slow:
	$(PYTHON) -m pytest_watch --verbose --ext=.py,.xsl -- -p no:cacheprovider $(ARGS)


dev-test: dev-lint dev-pytest


dev-start:
	$(PYTHON) -m sciencebeam.server $(ARGS)


dev-start-doc-to-pdf:
	$(PYTHON) -m sciencebeam.server --port=8075 --pipeline=doc_to_pdf $(ARGS)


dev-start-doc-to-docx:
	$(PYTHON) -m sciencebeam.server --port=8075 --pipeline=doc_to_docx $(ARGS)


build-dev:
	@if [ "$(NO_BUILD)" != "y" ]; then \
		$(DOCKER_COMPOSE) build sciencebeam-base-dev sciencebeam-dev; \
	fi


test: build-dev
	$(RUN_DEV) ./project_tests.sh


watch: build-dev
	$(RUN_DEV) pytest-watch --verbose --ext=.py,.xsl -- -p no:cacheprovider -k 'not slow' $(ARGS)


shell-dev: build-dev
	$(RUN_DEV) bash


start:
	$(DOCKER_COMPOSE) up -d --build grobid sciencebeam


start-doc-to-pdf:
	$(DOCKER_COMPOSE) build sciencebeam
	$(DOCKER_COMPOSE) run --rm --no-deps -p 8075:8075 sciencebeam \
		python -m sciencebeam.server --host=0.0.0.0 --port=8075 --pipeline=doc_to_pdf $(ARGS)


stop:
	$(DOCKER_COMPOSE) down


logs:
	$(DOCKER_COMPOSE) logs -f


ci-build-all:
	$(DOCKER_COMPOSE_CI) build


ci-test:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" test


ci-clean:
	$(DOCKER_COMPOSE_CI) down -v
