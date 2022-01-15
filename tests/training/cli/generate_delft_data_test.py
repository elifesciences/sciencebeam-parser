import logging
from pathlib import Path

from sciencebeam_parser.training.cli.generate_delft_data import (
    main
)

from tests.test_utils import log_on_exception


LOGGER = logging.getLogger(__name__)

MINIMAL_EXAMPLE_PDF = 'test-data/minimal-example.pdf'
MINIMAL_EXAMPLE_PDF_PATTERN = 'test-data/minimal-example*.pdf'


SOURCE_FILENAME_1 = 'test1.pdf'


@log_on_exception
class TestMain:
    def test_should_be_able_to_generate_segmentation_training_data(
        self,
        tmp_path: Path
    ):
        tei_source_path = tmp_path / 'tei'
        raw_source_path = tmp_path / 'raw'
        output_path = tmp_path / 'output.data'
        main([
            '--model-name=segmentation',
            f'--tei-source-path={tei_source_path}',
            f'--raw-source-path={raw_source_path}',
            f'--delft-output-path={output_path}'
        ])
        assert output_path.exists()
