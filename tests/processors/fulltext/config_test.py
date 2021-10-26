import pytest

from sciencebeam_parser.config.config import AppConfig
from sciencebeam_parser.processors.fulltext.config import (
    FullTextProcessorConfig,
    RequestFieldNames
)


EXTRACT_ALL_FULLTEXT_CONFIG = FullTextProcessorConfig(
    extract_body_sections=True,
    extract_acknowledgements=True,
    extract_back_sections=True,
    extract_references=True,
    extract_citation_fields=True,
    extract_citation_authors=True,
    extract_citation_editors=False,
    extract_figure_fields=True,
    extract_table_fields=True
)


class TestFullTextProcessorConfig:
    @pytest.mark.parametrize("field_name,value", [
        ("merge_raw_authors", False),
        ("merge_raw_authors", True)
    ])
    def test_should_override_default_from_app_config(self, field_name: str, value: bool):
        config = FullTextProcessorConfig.from_app_config(app_config=AppConfig(props={
            'processors': {
                'fulltext': {
                    field_name: value
                }
            }
        }))
        assert getattr(config, field_name) is value

    def test_should_ignore_empty_requested_field_names(self):
        config = EXTRACT_ALL_FULLTEXT_CONFIG.get_for_requested_field_names(set())
        assert config == EXTRACT_ALL_FULLTEXT_CONFIG

    def test_should_configure_only_header_extraction(self):
        config = EXTRACT_ALL_FULLTEXT_CONFIG.get_for_requested_field_names({
            RequestFieldNames.TITLE,
            RequestFieldNames.ABSTRACT,
            RequestFieldNames.AUTHORS,
            RequestFieldNames.AFFILIATIONS
        })
        assert config.extract_authors
        assert config.extract_affiliations
        assert not config.extract_body_sections
        assert not config.extract_acknowledgements
        assert not config.extract_back_sections
        assert not config.extract_references

    def test_should_configure_extract_references(self):
        config = EXTRACT_ALL_FULLTEXT_CONFIG.get_for_requested_field_names({
            RequestFieldNames.REFERENCES
        })
        assert not config.extract_authors
        assert not config.extract_affiliations
        assert not config.extract_body_sections
        assert not config.extract_acknowledgements
        assert not config.extract_back_sections
        assert config.extract_references

    def test_should_treat_unknown_field_names_as_no_change(self):
        config = EXTRACT_ALL_FULLTEXT_CONFIG.get_for_requested_field_names({
            'other'
        })
        assert config == EXTRACT_ALL_FULLTEXT_CONFIG
