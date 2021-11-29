from sciencebeam_parser.training.cli.generate_data import (
    main
)


class TestMain:
    def test_should_be_able_to_generate_segmentation_training_data(self):
        main([
            '--model="segmentation"',
            '--source-path="test-data/minimal-example.pdf"',
            '--output-path="./data/generated-training-data"'
        ])
