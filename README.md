# ScienceBeam Parser

ScienceBeam Parser allows you to parse scientific documents.
Initially is starting as a partial Python variation of GROBID and allows you to re-use some of the models.
However, it may deviate more in the future.

## Pre-requisites

This currently only supports Linux due to the binaries used (`pdfalto`).
Other plaforms are supported Docker.
It may also be used on other platforms without Docker, provided matching binaries are configured.

## Development

### Create Virtual Environment and install Dependencies

```bash
make dev-venv
```

### Configuration

There is no implicit "grobid-home" directory. The only configuration file is [config.yml](config.yml).

Paths may point to local or remote files. Remote files are downloaded and cached locally (urls are assumed to be versioned).

You may override config values using environment variables.
Environment variables should start with `SCIENCEBEAM_PARSER__`. After that `__` is used as a section separator.
For example `SCIENCEBEAM_PARSER__LOGGING__HANDLERS__LOG_FILE__LEVEL` would override `logging.handlers.log_file.level`.

### Run tests (linting, pytest, etc.)

```bash
make dev-test
```

### Start the server

```bash
make dev-start
```

Run the server in debug mode (including auto-reload and debug logging):

```bash
make dev-debug
```

Run the server with auto reload but no debug logging:

```bash
make dev-start-no-debug-logging-auto-reload
```

### Submit a sample document to the server

```bash
curl --fail --show-error \
    --form "file=@test-data/minimal-example.pdf;filename=test-data/minimal-example.pdf" \
    --silent "http://localhost:8080/api/pdfalto"
```

### Submit a sample document to the header model

The following output formats are supported:

| output_format | description |
| ------------- | ----- |
| raw_data | generated data (without using the model) |
| data | generated data with predicted labels |
| xml | using simple xml elements for predicted labels |
| json | json of prediction |

```bash
curl --fail --show-error \
    --form "file=@test-data/minimal-example.pdf;filename=test-data/minimal-example.pdf" \
    --silent "http://localhost:8080/api/models/header?first_page=1&last_page=1&output_format=xml"
```

### Submit a sample document to the name-header api

```bash
curl --fail --show-error \
    --form "file=@test-data/minimal-example.pdf;filename=test-data/minimal-example.pdf" \
    --silent "http://localhost:8080/api/models/name-header?first_page=1&last_page=1&output_format=xml"
```

### Submit a sample document to the full text api

```bash
curl --fail --show-error \
    --form "file=@test-data/minimal-example.pdf;filename=test-data/minimal-example.pdf" \
    --silent "http://localhost:8080/api/processFulltextDocument?first_page=1&last_page=1"
```

### Docker Usage

```bash
docker pull de4code/sciencebeam_parser-poc_unstable
```

```bash
docker run --rm \
    -p 8070:8070 \
    de4code/sciencebeam_parser-poc_unstable
```

## See also

* [architecture](ARCHITECTURE.md)
