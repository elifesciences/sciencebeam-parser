DOCKER_COMPOSE_DEV = docker-compose
DOCKER_COMPOSE_CI = docker-compose -f docker-compose.yml
DOCKER_COMPOSE = $(DOCKER_COMPOSE_DEV)


RUN_DEV = $(DOCKER_COMPOSE) run --rm sciencebeam-dev

NO_BUILD =
PYTEST_ARGS =


dev-venv:
	rm -rf venv || true

	virtualenv -p python2.7 venv

	venv/bin/pip install -r requirements.prereq.txt
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install -r requirements.py2.txt
	venv/bin/pip install -r requirements.dev.txt


build-dev:
	if [ "$(NO_BUILD)" != "y" ]; then \
		$(DOCKER_COMPOSE) build sciencebeam-base-dev sciencebeam-dev; \
	fi


test: build-dev
	$(RUN_DEV) ./project_tests.sh


watch: build-dev
	$(RUN_DEV) pytest-watch -- -p no:cacheprovider $(PYTEST_ARGS)


ci-build-all:
	$(DOCKER_COMPOSE_CI) build


ci-test:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" test


ci-clean:
	$(DOCKER_COMPOSE_CI) down -v
