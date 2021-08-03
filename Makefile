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


IMAGE_NAME = de4code/sciencebeam-parser_unstable
IMAGE_TAG = develop


SCIENCEBEAM_DELFT_MAX_SEQUENCE_LENGTH = 2000
SCIENCEBEAM_DELFT_INPUT_WINDOW_STRIDE = 1800
SCIENCEBEAM_DELFT_BATCH_SIZE = 1
SCIENCEBEAM_DELFT_STATEFUL = false


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


docker-build:
	docker build . -t $(IMAGE_NAME):$(IMAGE_TAG)


docker-run:
	docker run --rm \
		-p 8072:8070 \
		$(IMAGE_NAME):$(IMAGE_TAG) $(ARGS)
