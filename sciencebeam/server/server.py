import argparse
import logging

from flask import Flask
from flask_cors import CORS

from sciencebeam.config.app_config import get_app_config

from .blueprints.api import (
    create_api_blueprint,
    add_arguments as add_api_arguments
)

LOGGER = logging.getLogger(__name__)


def create_app(config, args):
    app = Flask(__name__)
    CORS(app)

    api = create_api_blueprint(config, args)
    app.register_blueprint(api, url_prefix='/api')

    return app


def initialize_logging():
    logging.basicConfig(level='DEBUG')
    logging.getLogger('summa.preprocessing.cleaner').setLevel(logging.WARNING)


def parse_args(config, argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--host', required=False,
        help='Host to bind server to.'
    )
    parser.add_argument(
        '--port', type=int, default=8080,
        help='The port to listen to.'
    )
    add_api_arguments(parser, config, argv=argv)
    parsed_args = parser.parse_args(argv)
    return parsed_args


def main(argv=None):
    config = get_app_config()
    args = parse_args(config, argv)
    app = create_app(config, args)
    app.run(port=args.port, host=args.host, threaded=True)


if __name__ == "__main__":
    main()
