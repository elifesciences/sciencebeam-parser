from sciencebeam_parser.models.model_impl_factory import (
    EngineNames,
    get_engine_name_for_config
)


class TestGetEngineNameForConfig:
    def test_should_return_wapiti_if_engine_prop_is_wapiti(self):
        assert get_engine_name_for_config({
            'engine': EngineNames.WAPITI
        }) == EngineNames.WAPITI

    def test_should_return_delft_without_engine_prop(self):
        assert get_engine_name_for_config({}) == EngineNames.DELFT

    def test_should_return_delft_if_engine_prop_is_blank(self):
        assert get_engine_name_for_config({
            'engine': ''
        }) == EngineNames.DELFT
