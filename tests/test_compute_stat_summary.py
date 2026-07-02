"""Tests for wakutils.compute_stat_summary — the aggregated stat rows
consumed by both WakfuItemStatSum and WakfuBuildManager._snapshot_stats.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import settings
from settings import simpleActionEnum, paramsActionEnum
from wakutils import compute_stat_summary

from tests.conftest import make_item


def _setup_items(items):
    """Load a dict of items into settings.ITEMS_DATA and provide labels
    in ACTION_DATA so effect strings resolve nicely."""
    settings.ITEMS_DATA = {i["definition"]["item"]["id"]: i for i in items}
    settings.ACTION_DATA = {
        int(simpleActionEnum.PV_ADD):            {"definition": {"effect": "Boost PV"}},
        int(simpleActionEnum.FIRE_MASTERY_ADD):  {"definition": {"effect": "Gain feu"}},
        int(paramsActionEnum.RANDOM_NUMBER_MASTERY_ADD): {"definition": {"effect": "Variable mastery"}},
    }


def _get_row(rows, effect_id):
    for r in rows:
        if r["effectId"] == effect_id:
            return r
    return None


class TestComputeStatSummary:
    def test_empty_item_list_returns_empty(self):
        _setup_items([])
        assert compute_stat_summary([]) == []

    def test_single_item_single_effect(self):
        item = make_item(1, 200, 134, 4, {int(simpleActionEnum.PV_ADD): [100, 0]})
        _setup_items([item])
        rows = compute_stat_summary([1])
        assert len(rows) == 1
        pv = rows[0]
        assert pv["effectId"] == int(simpleActionEnum.PV_ADD)
        assert pv["value"] == 100
        assert "Boost PV" in pv["effect"]
        assert "100" in pv["effect"]

    def test_sum_across_items(self):
        a = make_item(1, 200, 134, 4, {int(simpleActionEnum.PV_ADD): [80, 0]})
        b = make_item(2, 200, 136, 4, {int(simpleActionEnum.PV_ADD): [60, 0]})
        c = make_item(3, 200, 138, 4, {int(simpleActionEnum.PV_ADD): [20, 0]})
        _setup_items([a, b, c])
        rows = compute_stat_summary([1, 2, 3])
        pv = _get_row(rows, int(simpleActionEnum.PV_ADD))
        assert pv["value"] == 160

    def test_zero_sum_effect_is_omitted(self):
        """If total for an action is 0, no row is emitted (no noise)."""
        item = make_item(1, 200, 134, 4, {int(simpleActionEnum.PV_ADD): [0, 0]})
        _setup_items([item])
        rows = compute_stat_summary([1])
        assert _get_row(rows, int(simpleActionEnum.PV_ADD)) is None

    def test_multiple_effects_separated(self):
        item = make_item(1, 200, 134, 4, {
            int(simpleActionEnum.PV_ADD): [100, 0],
            int(simpleActionEnum.FIRE_MASTERY_ADD): [50, 0],
        })
        _setup_items([item])
        rows = compute_stat_summary([1])
        assert len(rows) == 2
        assert {r["effectId"] for r in rows} == {
            int(simpleActionEnum.PV_ADD),
            int(simpleActionEnum.FIRE_MASTERY_ADD),
        }

    def test_missing_item_id_is_skipped(self):
        """Stale saved builds may reference IDs no longer in ITEMS_DATA."""
        item = make_item(1, 200, 134, 4, {int(simpleActionEnum.PV_ADD): [100, 0]})
        _setup_items([item])
        rows = compute_stat_summary([1, 99999])
        assert _get_row(rows, int(simpleActionEnum.PV_ADD))["value"] == 100

    def test_params_action_includes_nb_element(self):
        """paramsActionEnum rows include ' on N element' in the effect string."""
        item = make_item(1, 200, 134, 4, {
            int(paramsActionEnum.RANDOM_NUMBER_MASTERY_ADD): [30, 0, 3],
        })
        _setup_items([item])
        rows = compute_stat_summary([1])
        assert len(rows) == 1
        row = rows[0]
        assert row["effectId"] == int(paramsActionEnum.RANDOM_NUMBER_MASTERY_ADD)
        assert "on 3 element" in row["effect"]

    def test_fallback_label_when_action_missing(self):
        """If ACTION_DATA has no entry for the action, use a generic label."""
        item = make_item(1, 200, 134, 4, {int(simpleActionEnum.PV_ADD): [100, 0]})
        settings.ITEMS_DATA = {1: item}
        settings.ACTION_DATA = {}          # empty on purpose
        rows = compute_stat_summary([1])
        assert rows[0]["effect"].startswith(f"Action {int(simpleActionEnum.PV_ADD)}")
