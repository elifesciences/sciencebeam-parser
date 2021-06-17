from pygrobid.models.delft_model import iter_entity_values_predicted_labels


class TestIterEntityValuesPredictedLabels:
    def test_should_extract_multiple_entity_values(self):
        tag_result = [
            ('The', 'B-<title>'),
            ('Title', 'I-<title>'),
            ('Some', 'B-<abstract>'),
            ('Abstract', 'I-<abstract>')
        ]
        assert list(iter_entity_values_predicted_labels(tag_result)) == [
            ('<title>', 'The Title'),
            ('<abstract>', 'Some Abstract')
        ]

    def test_should_extract_multiple_entity_values_including_none(self):
        tag_result = [
            ('The', 'B-<title>'),
            ('Title', 'I-<title>'),
            ('Other1', 'O'),
            ('Other2', 'O'),
            ('Some', 'B-<abstract>'),
            ('Abstract', 'I-<abstract>')
        ]
        assert list(iter_entity_values_predicted_labels(tag_result)) == [
            ('<title>', 'The Title'),
            ('O', 'Other1 Other2'),
            ('<abstract>', 'Some Abstract')
        ]
