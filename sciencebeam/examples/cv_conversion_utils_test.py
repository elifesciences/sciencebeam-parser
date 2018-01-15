import logging
from mock import patch

import sciencebeam.examples.cv_conversion_utils as cv_conversion_utils
from sciencebeam.examples.cv_conversion_utils import (
  InferenceModelWrapper
)

CV_MODEL_EXPORT_DIR = './model-export'
PNG_BYTES = b'dummy png bytes'

def setup_module():
  logging.basicConfig(level='DEBUG')

class TestInferenceModelWrapper(object):
  def test_should_lazy_load_model(self):
    with patch.object(cv_conversion_utils, 'load_inference_model') as load_inference_model:
      with patch.object(cv_conversion_utils, 'png_bytes_to_image_data') as png_bytes_to_image_data:
        with patch.object(cv_conversion_utils, 'tf') as tf:
          inference_model_wrapper = InferenceModelWrapper(CV_MODEL_EXPORT_DIR)
          load_inference_model.assert_not_called()

          output_image_data = inference_model_wrapper([PNG_BYTES])

          tf.InteractiveSession.assert_called_with()
          session = tf.InteractiveSession.return_value

          png_bytes_to_image_data.assert_called_with(PNG_BYTES)

          load_inference_model.assert_called_with(CV_MODEL_EXPORT_DIR, session=session)
          inference_model = load_inference_model.return_value

          inference_model.assert_called_with([
            png_bytes_to_image_data.return_value
          ], session=session)

          assert output_image_data == inference_model.return_value

  def test_should_load_model_only_once(self):
    with patch.object(cv_conversion_utils, 'load_inference_model') as load_inference_model:
      with patch.object(cv_conversion_utils, 'png_bytes_to_image_data') as _:
        with patch.object(cv_conversion_utils, 'tf') as _:
          inference_model_wrapper = InferenceModelWrapper(CV_MODEL_EXPORT_DIR)
          inference_model_wrapper([PNG_BYTES])
          inference_model_wrapper([PNG_BYTES])
          load_inference_model.assert_called_once()
