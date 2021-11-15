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

The server will start to listen on port `8080`.

The [default config.yml](../sciencebeam_parser/resources/default_config/config.yml) defines what models to load.

## Python API

### Python API: Start Server

```python
import logging

from sciencebeam_parser.config.config import AppConfig
from sciencebeam_parser.resources.default_config import DEFAULT_CONFIG_FILE
from sciencebeam_parser.service.server import create_app


config = AppConfig.load_yaml(DEFAULT_CONFIG_FILE)
app = create_app(config)
app.run(port=8080, host='127.0.0.1', threaded=True)
```

The server will start to listen on port `8080`.
