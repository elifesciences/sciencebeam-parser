# pylint: disable=not-callable
import logging
from pathlib import Path

from lxml import etree
from lxml.builder import E

from sciencebeam_trainer_delft.sequence_labelling.reader import (
    load_data_and_labels_crf_file
)
from sciencebeam_parser.training.cli.generate_delft_data import (
    main
)

from tests.test_utils import log_on_exception


LOGGER = logging.getLogger(__name__)

MINIMAL_EXAMPLE_PDF = 'test-data/minimal-example.pdf'
MINIMAL_EXAMPLE_PDF_PATTERN = 'test-data/minimal-example*.pdf'


SOURCE_FILENAME_1 = 'test1.pdf'


TOKEN_1 = 'token1'
TOKEN_2 = 'token2'
TOKEN_3 = 'token3'


@log_on_exception
class TestMain:
    def test_should_be_able_to_generate_segmentation_training_data(
        self,
        tmp_path: Path
    ):
        tei_source_path = tmp_path / 'tei'
        raw_source_path = tmp_path / 'raw'
        output_path = tmp_path / 'output.data'
        tei_source_path.mkdir(parents=True, exist_ok=True)
        (tei_source_path / 'sample.segmentation.tei.xml').write_bytes(etree.tostring(
            E('tei', E('text', *[
                E('front', TOKEN_1, E('lb')),
                '\n',
                E('back', TOKEN_2, E('lb')),
                '\n'
            ]))
        ))
        raw_source_path.mkdir(parents=True, exist_ok=True)
        (raw_source_path / 'sample.segmentation').write_text('\n'.join([
            '{TOKEN_1} 1.1 1.2 1.3',
            '{TOKEN_2} 2.1 2.2 2.3'
        ]))
        main([
            '--model-name=segmentation',
            f'--tei-source-path={tei_source_path}/*.tei.xml',
            f'--raw-source-path={raw_source_path}',
            f'--delft-output-path={output_path}'
        ])
        assert output_path.exists()
        texts, _labels, _features = load_data_and_labels_crf_file(
            str(output_path)
        )
        LOGGER.debug('texts: %r', texts)
        assert len(texts) == 1
        assert list(texts[0]) == [TOKEN_1, TOKEN_2]
        assert list(_labels[0]) == ['B-<front>', 'B-<back>']
        assert _features.tolist() == [[
            ['1.1', '1.2', '1.3'],
            ['2.1', '2.2', '2.3']
        ]]
