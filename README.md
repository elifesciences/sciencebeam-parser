# ScienceBeam Parser

ScienceBeam Parser allows you to parse scientific documents.
Initially is starting as a partial Python variation of GROBID and allows you to re-use some of the models.
However, it may deviate more in the future.

## Pre-requisites

This currently only supports Linux due to the binaries used (`pdfalto`, `wapiti`).
Other plaforms are supported via Docker.
It may also be used on other platforms without Docker, provided matching binaries are configured.

For Computer Vision PyTorch is required.

For OCR, tesseract needs to be installed. On Ubuntu the following command can be used:

```bash
apt-get install libtesseract4 tesseract-ocr-eng libtesseract-dev libleptonica-dev
```

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

The default response will be TEI XML (`application/tei+xml`).
The `Accept` HTTP request header may be used to request JATS, with the mime type `application/vnd.jats+xml`.

```bash
curl --fail --show-error \
    --header 'Accept: application/vnd.jats+xml' \
    --form "file=@test-data/minimal-example.pdf;filename=test-data/minimal-example.pdf" \
    --silent "http://localhost:8080/api/processFulltextDocument?first_page=1&last_page=1"
```

Regardless, the returned content type will be `application/xml`.

### Submit a sample document to the full text asset document api

The `processFulltextAssetDocument` is like `processFulltextDocument`. But instead of returning the TEI XML directly, it will contain a zip with the TEI XML document, along with other assets such as figure images.

```bash
curl --fail --show-error \
    --output "example-tei-xml-and-assets.zip" \
    --form "file=@test-data/minimal-example.pdf;filename=test-data/minimal-example.pdf" \
    --silent "http://localhost:8080/api/processFulltextAssetDocument?first_page=1&last_page=1"
```

The default response will be ZIP containing TEI XML (`application/tei+xml+zip`).
The `Accept` HTTP request header may be used to request a ZIP containing JATS,
with the mime type `application/vnd.jats+xml+zip`.

```bash
curl --fail --show-error \
    --header 'Accept: application/vnd.jats+xml+zip' \
    --output "example-jats-xml-and-assets.zip" \
    --form "file=@test-data/minimal-example.pdf;filename=test-data/minimal-example.pdf" \
    --silent "http://localhost:8080/api/processFulltextAssetDocument?first_page=1&last_page=1"
```

Regardless, the returned content type will be `application/zip`.

### Docker Usage

```bash
docker pull elifesciences/sciencebeam-parser
```

```bash
docker run --rm \
    -p 8070:8070 \
    elifesciences/sciencebeam-parser
```

Note: Docker images with the tag suffix `-cv` include the dependencies required for the CV (Computer Vision) models (disabled by default).

```bash
docker run --rm \
    -p 8070:8070 \
    --env SCIENCEBEAM_PARSER__PROCESSORS__FULLTEXT__USE_CV_MODEL=true \
    --env SCIENCEBEAM_PARSER__PROCESSORS__FULLTEXT__USE_OCR_MODEL=true \
    elifesciences/sciencebeam-parser:latest-cv
```

Non-release builds are available with the `_unstable` image suffix, e.g. `elifesciences/sciencebeam-parser_unstable`.

## See also

* [architecture](ARCHITECTURE.md)
