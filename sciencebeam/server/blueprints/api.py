import logging

from flask import Blueprint, jsonify, request, Response
from werkzeug.exceptions import BadRequest

from sciencebeam.pipeline_runners.simple_pipeline_runner import (
  create_simple_pipeline_runner_from_config,
  add_arguments as _add_arguments
)

LOGGER = logging.getLogger(__name__)

def add_arguments(parser, config, argv=None):
  _add_arguments(parser, config, argv=argv)

def create_api_blueprint(config, args):
  blueprint = Blueprint('api', __name__)

  pipeline_runner = create_simple_pipeline_runner_from_config(
    config, args
  )

  @blueprint.route("/")
  def _api_root():
    return jsonify({
      'links': {
      }
    })

  @blueprint.route("/convert", methods=['POST'])
  def _convert():
    if 'file' not in request.files:
      raise BadRequest()
    uploaded_file = request.files['file']
    pdf_filename = uploaded_file.filename
    pdf_content = uploaded_file.read()
    conversion_result = pipeline_runner.convert(
      pdf_content=pdf_content, pdf_filename=pdf_filename
    )
    LOGGER.debug('conversion_result: %s', conversion_result)
    xml_content = conversion_result['xml_content']
    LOGGER.debug('xml_content: %s', xml_content)
    return Response(xml_content, mimetype='text/xml')

  @blueprint.route("/convert", methods=['GET'])
  def _convert_form():
    return '''
    <!doctype html>
    <title>Convert PDF</title>
    <h1>Convert PDF</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

  return blueprint
