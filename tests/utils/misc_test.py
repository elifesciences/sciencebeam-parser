from itertools import islice

from sciencebeam_parser.utils.misc import iter_ids


class TestIterIds:
    def test_should_return_sequence_of_ids(self):
        assert list(islice(iter_ids('prefix'), 3)) == ['prefix0', 'prefix1', 'prefix2']
