# ScienceBeam Docker Containers

This section details using or building the docker images. You will need [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/).

## Run Latest Docker Container

Make sure you have the latest docker image by running:

```bash
docker pull elifesciences/sciencebeam
```

Note: add the `develop` tag to use the local image after building it (`docker-compose build`)

Clone this repository and run:

```bash
docker-compose -f docker-compose.latest.yml up
```

That will start GROBID and ScienceBeam docker containers. The [ScienceBeam API](API.md) will be available on port _8075_.

Alternatively run (the _--add-host_ parameter is used to prevent Crossref lookups):

```bash
docker run --rm --add-host api.crossref.org:127.0.0.1 -p 8070:8070 lfoppiano/grobid:0.5.1
```

and:

```bash
docker run --rm -i -t -p 8075:8075 --net=host elifesciences/sciencebeam \
  ./server.sh --host=0.0.0.0 --port=8075 --grobid-url http://localhost:8070/api
```

## Run Science Parse and ScienceBeam Docker Container

Run the [Science Parse](https://github.com/allenai/science-parse) and ScienceBeam docker container:

```bash
docker run --rm -p 8071:8080 allenai-docker-public-docker.bintray.io/s2/scienceparse:1.3.2
```

and:

```bash
docker run --rm -i -t -p 8075:8075 --net=host elifesciences/sciencebeam \
  ./server.sh --host=0.0.0.0 --port=8075 --pipeline=scienceparse --science-parse-url \
  http://localhost:8071/v1
```

## Run Science Parse V2 and ScienceBeam Docker Container

Run the [Science Parse V2](https://github.com/allenai/spv2) and ScienceBeam docker container:

```bash
docker run --rm -p 8073:8081 allenai-docker-public-docker.bintray.io/s2/spv2:2.10
```

and:

```bash
docker run --rm -i -t -p 8075:8075 --net=host elifesciences/sciencebeam:develop \
  ./server.sh --host=0.0.0.0 --port=8075 --pipeline=scienceparse \
  --science-parse-url http://localhost:8073/v1/json/pdf --no-science-parse-xslt
```

## Run CERMINE and ScienceBeam Docker Container

Run the [CERMINE](https://github.com/CeON/CERMINE) and ScienceBeam docker container:

```bash
docker run --rm -p 8072:8080 elifesciences/cermine:1.13
```

and:

```bash
docker run --rm -i -t -p 8075:8075 --net=host elifesciences/sciencebeam \
  ./server.sh --host=0.0.0.0 --port=8075 --pipeline=cermine --cermine-url \
  http://localhost:8072/extract.do
```

## Run meTypeset and ScienceBeam Docker Container

Run the [meTypeset](https://github.com/MartinPaulEve/meTypeset) and ScienceBeam docker container:

```bash
docker run --rm -i -t -p 8074:8080 elifesciences/metypeset:latest
```

and:

```bash
docker run --rm -i -t -p 8075:8075 --net=host elifesciences/sciencebeam \
  ./server.sh --host=0.0.0.0 --port=8075 --pipeline=metypeset --metypeset-url \
  http://localhost:8074/api/convert
```

## Build and Run Docker Container with Docker Compose

```bash
docker-compose -f docker-compose.yml build
```

```bash
docker-compose -f docker-compose.yml up
```

That will start GROBID and ScienceBeam docker containers. The [ScienceBeam API](API.md) will be available on port _8075_.

## Build Docker Container Only

```bash
./build_container.sh
```

## GROBID and Crossref Consolidation

GROBID is optionally using Crossref consolidation to make the results more useful for archiving.

For this project, the preference is not to enable it and the _docker-compose.yml*_ files explictly use a local network to prevent that.
