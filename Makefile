DOCKER_COMPOSE_DEV = docker-compose
DOCKER_COMPOSE_CI = docker-compose -f docker-compose.yml
DOCKER_COMPOSE = $(DOCKER_COMPOSE_DEV)

VENV = venv
PIP = $(VENV)/bin/pip
PYTHON = $(VENV)/bin/python

RUN_DEV = $(DOCKER_COMPOSE) run --rm sciencebeam-dev

SCIENCEBEAM_PORT = 8075
CONVERT_API_URL = http://localhost:$(SCIENCEBEAM_PORT)/api/convert
EXAMPLE_DOCUMENT = test-data/minimal-office-open.docx

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


build:
	$(DOCKER_COMPOSE) build sciencebeam


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


build-and-start:
	$(DOCKER_COMPOSE) up -d --build grobid sciencebeam


start:
	$(DOCKER_COMPOSE) up -d grobid sciencebeam


start-doc-to-pdf:
	$(DOCKER_COMPOSE) build sciencebeam
	$(DOCKER_COMPOSE) run --rm --no-deps -p 8075:8075 sciencebeam \
		python -m sciencebeam.server --host=0.0.0.0 --port=8075 --pipeline=doc_to_pdf $(ARGS)


convert-example-document:
	curl --fail --show-error \
			--form "file=@$(EXAMPLE_DOCUMENT);filename=$(EXAMPLE_DOCUMENT)" \
			--silent "$(CONVERT_API_URL)" \
			> /dev/null


wait-for-sciencebeam:
	$(DOCKER_COMPOSE) run --rm wait-for-it \
		"sciencebeam:$(SCIENCEBEAM_PORT)" \
		--timeout=10 \
		--strict \
		-- echo "ScienceBeam is up"


wait-for-grobid:
	$(DOCKER_COMPOSE) run --rm wait-for-it \
		"grobid:8070" \
		--timeout=10 \
		--strict \
		-- echo "GROBID is up"


end-to-end-test:
	$(MAKE) start
	$(MAKE) wait-for-sciencebeam wait-for-grobid
	$(MAKE) convert-example-document
	$(MAKE) stop


stop:
	$(DOCKER_COMPOSE) down


logs:
	$(DOCKER_COMPOSE) logs -f


ci-build-all:
	$(DOCKER_COMPOSE_CI) build


ci-test:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" test


ci-end-to-end-test:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" end-to-end-test


ci-clean:
	$(DOCKER_COMPOSE_CI) down -v
