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

GROBID_HOME = ./grobid-home

PYGROBID_PORT = 8080

PDFALTO_CONVERT_API_URL = http://localhost:$(PYGROBID_PORT)/api/pdfalto
EXAMPLE_PDF_DOCUMENT = test-data/minimal-example.pdf


PDFALTO_BINARY_PATH = grobid-home/pdf2xml/lin-64/pdfalto
GROBID_HOME_BASE_DOWNLOAD_URL = https://github.com/kermitt2/grobid/raw/0.6.2/grobid-home
# PDFALTO_BINARY_DOWNLOAD_URL = $(GROBID_HOME_BASE_DOWNLOAD_URL)/pdf2xml/lin-64/pdfalto
PDFALTO_BINARY_DOWNLOAD_URL = https://github.com/kermitt2/pdfalto/files/6104204/pdfalto-4b4e983413278a07bb4cc4b2836de03adc8ca6dc-dockcross-linux-64.gz


IMAGE_NAME = de4code/pygrobid-poc_unstable
IMAGE_TAG = develop


SCIENCEBEAM_DELFT_MAX_SEQUENCE_LENGTH = 2000
SCIENCEBEAM_DELFT_INPUT_WINDOW_STRIDE = 1800


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


download-pdfalto:
	@echo "downloading: $(PDFALTO_BINARY_DOWNLOAD_URL)"
	mkdir -p "$(dir $(PDFALTO_BINARY_PATH))"
	$(PYTHON) -m sciencebeam_trainer_delft.sequence_labelling.tools.install_file \
		--source="${PDFALTO_BINARY_DOWNLOAD_URL}" \
		--target="${PDFALTO_BINARY_PATH}"


grobid-home-setup:
	@if [ ! -f "$(PDFALTO_BINARY_PATH)" ]; then \
		$(MAKE) download-pdfalto; \
	fi
	chmod u+x "$(PDFALTO_BINARY_PATH)"


dev-flake8:
	$(PYTHON) -m flake8 pygrobid tests setup.py


dev-pylint:
	$(PYTHON) -m pylint pygrobid tests setup.py


dev-mypy:
	$(PYTHON) -m mypy --ignore-missing-imports pygrobid tests setup.py


dev-lint: dev-flake8 dev-pylint dev-mypy


dev-pytest:
	$(PYTHON) -m pytest -p no:cacheprovider $(ARGS)


dev-watch:
	$(PYTHON) -m pytest_watch -- -p no:cacheprovider -p no:warnings $(ARGS)


dev-test: dev-lint dev-pytest


dev-start:
	GROBID_HOME=$(GROBID_HOME) \
	SCIENCEBEAM_DELFT_MAX_SEQUENCE_LENGTH=$(SCIENCEBEAM_DELFT_MAX_SEQUENCE_LENGTH) \
	SCIENCEBEAM_DELFT_INPUT_WINDOW_STRIDE=$(SCIENCEBEAM_DELFT_INPUT_WINDOW_STRIDE) \
		$(PYTHON) -m pygrobid.service.server --port=$(PYGROBID_PORT)


dev-start-debug:
	FLASK_ENV=development \
	$(MAKE) dev-start


dev-end-to-end:
	curl --fail --show-error \
		--form "file=@$(EXAMPLE_PDF_DOCUMENT);filename=$(EXAMPLE_PDF_DOCUMENT)" \
		--silent "$(PDFALTO_CONVERT_API_URL)" \
		> /dev/null


run:
	$(PYTHON) -m pygrobid $(ARGS)


docker-build:
	docker build . -t $(IMAGE_NAME):$(IMAGE_TAG)


docker-run:
	docker run --rm \
		-p 8072:8070 \
		$(IMAGE_NAME):$(IMAGE_TAG) $(ARGS)
