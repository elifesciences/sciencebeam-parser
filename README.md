# PyGrobid

A python version of GROBID (proof-of-concept).
This currently only supports Linux.

## Development

### Create Virtual Environment and install Dependencies

```bash
make dev-venv
```

### Setup grobid-home

```bash
make grobid-home-setup
```

### Run tests (linting, pytest, etc.)

```bash
make dev-test
```

### Start the server

```bash
make dev-start
```

### Submit a sample document to the server

```bash
curl --fail --show-error \
    --form "file=@test-data/minimal-example.pdf;filename=test-data/minimal-example.pdf" \
    --silent "http://localhost:8080/api/pdfalto"
```
