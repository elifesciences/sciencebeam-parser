import logging

from flask import Blueprint, jsonify

LOGGER = logging.getLogger(__name__)

def create_api_blueprint(_):
  blueprint = Blueprint('api', __name__)

  @blueprint.route("/")
  def _api_root():
    return jsonify({
      'links': {
      }
    })

  return blueprint
