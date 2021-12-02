import os
from pathlib import Path

from sciencebeam_parser.models.segmentation.training_data import (
    SegmentationTeiTrainingDataGenerator
)
from sciencebeam_parser.training.cli.generate_data import (
    main
)


MINIMAL_EXAMPLE_PDF = 'test-data/minimal-example.pdf'
MINIMAL_EXAMPLE_PDF_PATTERN = 'test-data/minimal-example*.pdf'


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
