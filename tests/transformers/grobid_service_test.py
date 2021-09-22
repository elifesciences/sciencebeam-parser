from unittest.mock import patch, ANY

import pytest

from sciencebeam.transformers.grobid_service import (
    GrobidServiceConfigEnvVariables,
    GrobidServiceConfig,
    get_grobid_service_config,
    get_request_data_for_config,
    grobid_service as create_grobid_service
)


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


@pytest.fixture(name='environ', autouse=True)
def _mock_environ():
    with patch('os.environ', {}) as mock:
        yield mock


@pytest.fixture(name='grobid_service_config')
def _grobid_service_config() -> GrobidServiceConfig:
    return GrobidServiceConfig()


class TestGetGrobidServiceConfig:
    def test_should_return_default_config(self):
        config = get_grobid_service_config()
        assert not config.consolidate_header
        assert not config.consolidate_citations
        assert config.include_raw_affiliations
        assert config.include_raw_citations
        assert config.include_coordinates

    def test_should_be_able_toggle_config(self, environ: dict):
        environ[GrobidServiceConfigEnvVariables.CONSOLIDATE_HEADER] = '1'
        environ[GrobidServiceConfigEnvVariables.CONSOLIDATE_CITATIONS] = '1'
        environ[GrobidServiceConfigEnvVariables.INCLUDE_RAW_AFFILIATIONS] = '0'
        environ[GrobidServiceConfigEnvVariables.INCLUDE_RAW_CITATIONS] = '0'
        environ[GrobidServiceConfigEnvVariables.INCLUDE_COORDINATES] = '0'
        config = get_grobid_service_config()
        assert config.consolidate_header
        assert config.consolidate_citations
        assert not config.include_raw_affiliations
        assert not config.include_raw_citations
        assert not config.include_coordinates


class TestGetRequestDataForConfig:
    def test_should_generate_dict_for_default_config(self):
        grobid_service_config = GrobidServiceConfig(
            consolidate_header=False,
            consolidate_citations=False,
            include_raw_affiliations=True,
            include_raw_citations=True
        )
        assert get_request_data_for_config(grobid_service_config) == {
            'consolidateHeader': '0',
            'consolidateCitations': '0',
            'includeRawAffiliations': '1',
            'includeRawCitations': '1'
        }


class TestCreateGrobidService:
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
        create_grobid_service(  # pylint: disable=redundant-keyword-arg
            BASE_URL, PATH_1, start_service=False
        )(
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
                'consolidateCitations': '0',
                'includeRawAffiliations': '1',
                'includeRawCitations': '1'
            }
        )
