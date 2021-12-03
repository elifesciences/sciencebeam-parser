import logging
import os
from pathlib import Path

import pytest

from lxml import etree

from sciencebeam_parser.utils.xml import get_text_content_list
from sciencebeam_parser.models.segmentation.training_data import (
    SegmentationTeiTrainingDataGenerator
)
from sciencebeam_parser.training.cli.generate_data import (
    main
)


LOGGER = logging.getLogger(__name__)

MINIMAL_EXAMPLE_PDF = 'test-data/minimal-example.pdf'
MINIMAL_EXAMPLE_PDF_PATTERN = 'test-data/minimal-example*.pdf'


# Note: tests are currently using actual model and are therefore slow
@pytest.mark.slow
class TestMain:
    def test_should_be_able_to_generate_segmentation_training_data(
        self,
        tmp_path: Path
    ):
        output_path = tmp_path / 'generated-data'
        main([
            f'--source-path={MINIMAL_EXAMPLE_PDF_PATTERN}',
            f'--output-path={output_path}'
        ])
        assert output_path.exists()
        example_name = os.path.splitext(os.path.basename(MINIMAL_EXAMPLE_PDF))[0]
        expected_segmentation_tei_path = output_path.joinpath(
            example_name + SegmentationTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )
        expected_segmentation_data_path = output_path.joinpath(
            example_name + SegmentationTeiTrainingDataGenerator.DEFAULT_DATA_FILENAME_SUFFIX
        )
        assert expected_segmentation_tei_path.exists()
        assert expected_segmentation_data_path.exists()
        xml_root = etree.parse(str(expected_segmentation_tei_path)).getroot()
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        assert get_text_content_list(xml_root.xpath('text'))
        assert not get_text_content_list(xml_root.xpath('text/front'))

    def test_should_be_able_to_generate_segmentation_training_data_using_model(
        self,
        tmp_path: Path
    ):
        output_path = tmp_path / 'generated-data'
        main([
            f'--source-path={MINIMAL_EXAMPLE_PDF_PATTERN}',
            f'--output-path={output_path}',
            '--use-model'
        ])
        assert output_path.exists()
        example_name = os.path.splitext(os.path.basename(MINIMAL_EXAMPLE_PDF))[0]
        expected_segmentation_tei_path = output_path.joinpath(
            example_name + SegmentationTeiTrainingDataGenerator.DEFAULT_TEI_FILENAME_SUFFIX
        )
        expected_segmentation_data_path = output_path.joinpath(
            example_name + SegmentationTeiTrainingDataGenerator.DEFAULT_DATA_FILENAME_SUFFIX
        )
        assert expected_segmentation_tei_path.exists()
        assert expected_segmentation_data_path.exists()
        xml_root = etree.parse(str(expected_segmentation_tei_path)).getroot()
        LOGGER.debug('xml: %r', etree.tostring(xml_root))
        assert get_text_content_list(xml_root.xpath('text/front'))
