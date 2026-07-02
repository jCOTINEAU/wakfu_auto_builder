"""Tests for wakfuBuildComparison._pair_slot — per-slot A/B pairing.

Pure function: given two lists of item IDs that share a slot, produce
(a_id, b_id, status) rows where status ∈ {equal, diff, onlyA, onlyB}.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wakfuBuildComparison import _pair_slot


class TestPairSlot:
    def test_both_empty(self):
        assert _pair_slot([], []) == []

    def test_only_a(self):
        assert _pair_slot([10], []) == [(10, None, "onlyA")]

    def test_only_b(self):
        assert _pair_slot([], [20]) == [(None, 20, "onlyB")]

    def test_both_same_singleton(self):
        assert _pair_slot([42], [42]) == [(42, 42, "equal")]

    def test_both_different_singleton(self):
        assert _pair_slot([1], [2]) == [(1, 2, "diff")]

    def test_rings_all_shared(self):
        rows = _pair_slot([100, 200], [100, 200])
        assert rows == [(100, 100, "equal"), (200, 200, "equal")]

    def test_rings_one_shared_one_diff(self):
        rows = _pair_slot([100, 200], [100, 300])
        # 100 matches first (equal), then 200 vs 300 (diff by position).
        assert rows == [(100, 100, "equal"), (200, 300, "diff")]

    def test_rings_no_shared(self):
        rows = _pair_slot([1, 2], [3, 4])
        # Position pairing.
        assert rows == [(1, 3, "diff"), (2, 4, "diff")]

    def test_asymmetric_extra_on_a(self):
        rows = _pair_slot([1, 2, 3], [1])
        # 1 matches (equal), leftover [2, 3] on A only.
        assert rows == [(1, 1, "equal"), (2, None, "onlyA"), (3, None, "onlyA")]

    def test_asymmetric_extra_on_b(self):
        rows = _pair_slot([1], [1, 2])
        assert rows == [(1, 1, "equal"), (None, 2, "onlyB")]

    def test_order_of_a_preserved_for_equal(self):
        """Equals are emitted in the order they appear in items_a_slot."""
        rows = _pair_slot([300, 100, 200], [100, 200, 300])
        # All three are equal, but ordering follows list_a.
        assert rows == [
            (300, 300, "equal"),
            (100, 100, "equal"),
            (200, 200, "equal"),
        ]
