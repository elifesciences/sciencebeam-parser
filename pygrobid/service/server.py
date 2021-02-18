import argparse
import logging

from flask import Flask

from pygrobid.service.blueprints.index import IndexBlueprint
from pygrobid.service.blueprints.api import ApiBlueprint


def create_app():
    app = Flask(__name__)

    index = IndexBlueprint()
    app.register_blueprint(index, url_prefix='/')

    api = ApiBlueprint()
    app.register_blueprint(api, url_prefix='/api')

    return app


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
    app = create_app()
    app.run(port=args.port, host=args.host, threaded=True)


if __name__ == "__main__":
    logging.basicConfig(level='INFO')
    main()
