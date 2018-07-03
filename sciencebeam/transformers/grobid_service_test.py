from mock import patch, ANY

import pytest

from .grobid_service import grobid_service as create_grobid_service

BASE_URL = 'http://grobid/api'
PATH_1 = '/path1'
PATH_2 = '/path2'

FILENAME_1 = 'file1.pdf'
PDF_CONTENT_1 = b'pdf content1'

FIELD_NAME_1 = 'field1'
FIELD_VALUE_1 = 'value1'

@pytest.fixture(name='requests_post', autouse=True)
def _mock_requests_post():
  with patch('requests.post') as requests_post:
    yield requests_post

class TestCreateGrobidService(object):
  def test_should_pass_url_and_data_as_file(self, requests_post):
    create_grobid_service(BASE_URL, PATH_1, start_service=False)(
      (FILENAME_1, PDF_CONTENT_1)
    )
    requests_post.assert_called_with(
      BASE_URL + PATH_1,
      files=ANY,
      data=ANY
    )
    kwargs = requests_post.call_args[1]
    assert kwargs['files']['input'][0] == FILENAME_1
    assert kwargs['files']['input'][1].read() == PDF_CONTENT_1

  def test_should_be_able_to_override_path_on_call(self, requests_post):
    create_grobid_service(BASE_URL, PATH_1, start_service=False)(
      (FILENAME_1, PDF_CONTENT_1),
      path=PATH_2
    )
    requests_post.assert_called_with(
      BASE_URL + PATH_2,
      files=ANY,
      data=ANY
    )

  def test_should_pass_data_as_field(self, requests_post):
    create_grobid_service(BASE_URL, PATH_1, start_service=False, field_name=FIELD_NAME_1)(
      FIELD_VALUE_1
    )
    requests_post.assert_called_with(
      BASE_URL + PATH_1,
      data={FIELD_NAME_1: FIELD_VALUE_1}
    )

  def test_should_pass_consolidate_flags(self, requests_post):
    create_grobid_service(BASE_URL, PATH_1, start_service=False)(
      (FILENAME_1, PDF_CONTENT_1)
    )
    requests_post.assert_called_with(
      BASE_URL + PATH_1,
      files=ANY,
      data={
        'consolidateHeader': '0',
        'consolidateCitations': '0'
      }
    )
