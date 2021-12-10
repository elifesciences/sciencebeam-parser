from sciencebeam_parser.models.training_data import (
    is_same_or_parent_path_of
)


class TestIsSameOrParentPathOf:
    def test_should_return_true_for_same_path(self):
        assert is_same_or_parent_path_of(['parent', 'child1'], ['parent', 'child1']) is True

    def test_should_return_true_for_parent_path_of_child(self):
        assert is_same_or_parent_path_of(['parent'], ['parent', 'child1']) is True

    def test_should_return_false_for_child_path_of_parent(self):
        assert is_same_or_parent_path_of(['parent', 'child1'], ['parent']) is False

    def test_should_return_false_for_siblings(self):
        assert is_same_or_parent_path_of(['parent', 'child1'], ['parent', 'child2']) is False

    def test_should_return_false_for_different_parent(self):
        assert is_same_or_parent_path_of(['parent1', 'child1'], ['parent2', 'child1']) is False
