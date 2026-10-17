"""Tests for the Alignment of predicted items with expected ones."""

from assayer.alignment import align_best_match, align_by_key, align_positional


def test_positional_pairs_same_index_and_leaves_the_rest_unmatched():
    alignment = align_positional(3, 2)

    assert alignment.pairs == [(0, 0), (1, 1)]
    assert (alignment.unmatched_expected, alignment.unmatched_predicted) == ([2], [])


def test_by_key_pairs_equal_keys_and_repeats_take_the_earliest_unpaired():
    expected = [{"id": 1}, {"id": 2}, {"id": 1}]
    predicted = [{"id": 2}, {"id": 1}, {"id": 1}, {"id": 9}]

    alignment = align_by_key(expected, predicted, "id")

    assert alignment.pairs == [(0, 1), (1, 0), (2, 2)]
    assert alignment.unmatched_predicted == [3]


def test_by_key_leaves_an_item_without_a_key_unpaired():
    alignment = align_by_key([{"x": 1}], [{"id": 1}], "id")

    assert (alignment.unmatched_expected, alignment.unmatched_predicted) == ([0], [0])


def test_best_match_is_greedy_by_similarity_above_the_threshold():
    similarity = {(0, 0): 0.4, (0, 1): 0.9, (1, 0): 0.8, (1, 1): 0.9}

    alignment = align_best_match(2, 2, lambda e, p: similarity[e, p], threshold=0.5)

    assert alignment.pairs == [(0, 1), (1, 0)]  # ties go to the lower position


def test_best_match_never_pairs_below_the_threshold():
    alignment = align_best_match(1, 1, lambda e, p: 0.4, threshold=0.5)

    assert alignment.pairs == []
    assert alignment.as_dict()["unmatched_expected"] == [0]
