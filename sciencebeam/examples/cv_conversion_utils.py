from __future__ import absolute_import

from io import BytesIO

import tensorflow as tf
import numpy as np

from PIL import Image

from sciencebeam_gym.inference_model import (
  load_inference_model
)

def lazy_cached_value(value_fn):
  cache = {}
  def wrapper():
    value = cache.get('value')
    if value is None:
      value = value_fn()
      cache['value'] = value
    return value
  return wrapper

def image_data_to_png(image_data):
  image = Image.fromarray(image_data, 'RGB')
  out = BytesIO()
  image.save(out, 'png')
  return out.getvalue()

def png_bytes_to_image_data(png_bytes):
  return np.asarray(Image.open(BytesIO(png_bytes)).convert('RGB'), dtype=np.uint8)

class InferenceModelWrapper(object):
  def __init__(self, export_dir):
    self.session_cache = lazy_cached_value(lambda: tf.InteractiveSession())
    self.inference_model_cache = lazy_cached_value(
      lambda: load_inference_model(export_dir, session=self.session_cache())
    )

  def get_color_map(self):
    return self.inference_model_cache().get_color_map(session=self.session_cache())

  def __call__(self, png_pages):
    input_data = [
      png_bytes_to_image_data(png_page)
      for png_page in png_pages
    ]
    output_img_data_batch = self.inference_model_cache()(input_data, session=self.session_cache())
    return output_img_data_batch
