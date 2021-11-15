# ScienceBeam Parser Python Library

ScienceBeam Parser allows you to parse scientific documents. It provides a REST API Service, as well as a Python API.

## Installation

```bash
pip install sciencebeam-parser
```

## CLI

### CLI: Start Server

```bash
python -m sciencebeam_parser.service.server --port=8080
```

The server will start to listen on port 8080.

The [default config.yml](../sciencebeam_parser/resources/default_config/config.yml) defines what models to load.
