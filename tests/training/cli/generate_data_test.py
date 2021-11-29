from pathlib import Path

from sciencebeam_parser.training.cli.generate_data import (
    main
)


class TestMain:
    def test_should_be_able_to_generate_segmentation_training_data(
        self,
        tmp_path: Path
    ):
        output_path = tmp_path / 'generated-data'
        main([
            '--model="segmentation"',
            '--source-path="test-data/minimal-example.pdf"',
            f'--output-path={output_path}'
        ])
        assert output_path.exists()
