import argparse
import logging
import os
from logging.config import dictConfig

from flask import Flask

from sciencebeam_parser.app.parser import ScienceBeamParser
from sciencebeam_parser.config.config import AppConfig
from sciencebeam_parser.service.blueprints.index import IndexBlueprint
from sciencebeam_parser.service.blueprints.api import ApiBlueprint
from sciencebeam_parser.resources.default_config import DEFAULT_CONFIG_FILE


LOGGER = logging.getLogger(__name__)


def create_app_for_parser(
    sciencebeam_parser: ScienceBeamParser
):
    app = Flask(__name__)

    index = IndexBlueprint()
    app.register_blueprint(index, url_prefix='/')

    api = ApiBlueprint(sciencebeam_parser)
    app.register_blueprint(api, url_prefix='/api')

    return app


def create_app_for_config(config: AppConfig):
    return create_app_for_parser(
        ScienceBeamParser.from_config(config)
    )


def create_app(config: AppConfig):
    return create_app_for_config(config)


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--host', required=False,
        help='Host to bind server to.'
    )
    parser.add_argument(
        '--port', type=int, default=8080,
        help='The port to listen to.'
    )
    parsed_args = parser.parse_args(argv)
    return parsed_args


def main(argv=None):
    args = parse_args(argv)
    config = AppConfig.load_yaml(DEFAULT_CONFIG_FILE).apply_environment_variables()
    logging_config = config.get('logging')
    if logging_config:
        for handler_config in logging_config.get('handlers', {}).values():
            filename = handler_config.get('filename')
            if not filename:
                continue
            dirname = os.path.dirname(filename)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
        try:
            dictConfig(logging_config)
        except ValueError:
            LOGGER.info('logging_config: %r', logging_config)
            raise
    LOGGER.info('app config: %s', config)
    app = create_app_for_config(config)
    app.run(port=args.port, host=args.host, threaded=True)


if __name__ == "__main__":
    logging.basicConfig(level='INFO')
    main()
