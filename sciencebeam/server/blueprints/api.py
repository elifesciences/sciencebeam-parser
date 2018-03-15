import logging

from flask import Blueprint, jsonify, request, Response
from werkzeug.exceptions import BadRequest

from sciencebeam.pipeline_factories.simple_pipeline import create_simple_pipeline_from_config

LOGGER = logging.getLogger(__name__)

def create_api_blueprint(config):
  blueprint = Blueprint('api', __name__)

  pipeline = create_simple_pipeline_from_config(config)

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
    conversion_result = pipeline.convert(
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
