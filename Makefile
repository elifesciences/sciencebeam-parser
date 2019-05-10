DOCKER_COMPOSE_DEV = docker-compose
DOCKER_COMPOSE_CI = docker-compose -f docker-compose.yml
DOCKER_COMPOSE = $(DOCKER_COMPOSE_DEV)


RUN_DEV = $(DOCKER_COMPOSE) run --rm sciencebeam-dev

NO_BUILD =


build-dev:
	if [ "$(NO_BUILD)" != "y" ]; then \
		$(DOCKER_COMPOSE) build sciencebeam-dev; \
	fi


test: build-dev
	$(RUN_DEV) ./project_tests.sh


ci-test:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" test


ci-clean:
	$(DOCKER_COMPOSE_CI) down -v
