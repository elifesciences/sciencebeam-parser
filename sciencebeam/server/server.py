import argparse
import logging

from flask import Flask
from flask_cors import CORS

from .blueprints.api import create_api_blueprint

LOGGER = logging.getLogger(__name__)

def create_app(args):
  app = Flask(__name__)
  CORS(app)

  api = create_api_blueprint(args)
  app.register_blueprint(api, url_prefix='/api')

  return app

def initialize_logging():
  logging.basicConfig(level='DEBUG')
  logging.getLogger('summa.preprocessing.cleaner').setLevel(logging.WARNING)

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
  app = create_app(args)
  app.run(port=args.port, host=args.host, threaded=True)

if __name__ == "__main__":
  main()
