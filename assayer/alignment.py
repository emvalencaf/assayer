"""Alignment: the pairing of predicted list items with expected ones."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from assayer.path import resolve


@dataclass
class Alignment:
    """Which predicted item answers which expected one.

    Args:
        pairs: `(expected_index, predicted_index)`, ordered by expected index.
        unmatched_expected: Indexes of expected items nothing was paired with (missing).
        unmatched_predicted: Indexes of predicted items nothing was paired with (extra).
    """

    pairs: list[tuple[int, int]]
    unmatched_expected: list[int]
    unmatched_predicted: list[int]

    def as_dict(self) -> dict[str, list]:
        """Return the Alignment as plain data, for a Score's metadata."""
        return {
            "pairs": [list(pair) for pair in self.pairs],
            "unmatched_expected": list(self.unmatched_expected),
            "unmatched_predicted": list(self.unmatched_predicted),
        }


def _build(pairs: list[tuple[int, int]], n_expected: int, n_predicted: int) -> Alignment:
    pairs = sorted(pairs)
    paired_e = {e for e, _ in pairs}
    paired_p = {p for _, p in pairs}
    return Alignment(
        pairs,
        [i for i in range(n_expected) if i not in paired_e],
        [i for i in range(n_predicted) if i not in paired_p],
    )


def align_positional(n_expected: int, n_predicted: int) -> Alignment:
    """Pair the items at the same index."""
    return _build([(i, i) for i in range(min(n_expected, n_predicted))], n_expected, n_predicted)


def align_by_key(expected: Sequence[Any], predicted: Sequence[Any], key: str) -> Alignment:
    """Pair items whose `key` property is equal; an item without a key is unpaired.

    A key repeated among the predicted items pairs with the earliest unpaired one.
    """
    pairs = []
    taken: set[int] = set()
    for e, item in enumerate(expected):
        wanted = resolve(item, key)
        if wanted is None:
            continue
        for p, candidate in enumerate(predicted):
            if p not in taken and resolve(candidate, key) == wanted:
                pairs.append((e, p))
                taken.add(p)
                break
    return _build(pairs, len(expected), len(predicted))


def align_best_match(
    n_expected: int,
    n_predicted: int,
    similarity: Callable[[int, int], float],
    threshold: float,
) -> Alignment:
    """Greedily pair by descending similarity, ties by position.

    Args:
        n_expected: Number of expected items.
        n_predicted: Number of predicted items.
        similarity: Similarity in [0, 1] of an (expected, predicted) index pair.
        threshold: Pairs with a lower similarity are never made.
    """
    candidates = sorted(
        ((e, p, similarity(e, p)) for e in range(n_expected) for p in range(n_predicted)),
        key=lambda c: (-c[2], c[0], c[1]),
    )
    pairs: list[tuple[int, int]] = []
    used_e: set[int] = set()
    used_p: set[int] = set()
    for e, p, score in candidates:
        if score < threshold:
            break
        if e not in used_e and p not in used_p:
            pairs.append((e, p))
            used_e.add(e)
            used_p.add(p)
    return _build(pairs, n_expected, n_predicted)
