import dataclasses
from unittest.mock import MagicMock

from sciencebeam_parser.processors.fulltext.models import FullTextModels


class TestFullTextModels:
    def test_should_preload_models(self):
        mock_models = {
            field.name: MagicMock(name=field.name)
            for field in dataclasses.fields(FullTextModels)
        }
        mock_fulltext_models = FullTextModels(**mock_models)
        mock_fulltext_models.preload()
        for model in mock_models.values():
            model.preload.assert_called()
