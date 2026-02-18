"""Tests for build comparison logic in build_manager.compare_builds."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import build_manager


@pytest.fixture
def build_a():
    return {
        "id": "aaa",
        "name": "Build Eau/Air",
        "items": [
            {"id": 1, "name": "Casque A"},
            {"id": 2, "name": "Plastron A"},
            {"id": 3, "name": "Anneau A"},
        ],
        "stats": [
            {"effect": "PV : 1200", "effectId": 20, "value": 1200},
            {"effect": "PA : 6", "effectId": 31, "value": 6},
            {"effect": "Maîtrise Eau : 800", "effectId": 124, "value": 800},
            {"effect": "Maîtrise Air : 400", "effectId": 125, "value": 400},
        ],
    }


@pytest.fixture
def build_b():
    return {
        "id": "bbb",
        "name": "Build Feu",
        "items": [
            {"id": 1, "name": "Casque A"},
            {"id": 4, "name": "Plastron B"},
            {"id": 5, "name": "Anneau B"},
        ],
        "stats": [
            {"effect": "PV : 1500", "effectId": 20, "value": 1500},
            {"effect": "PA : 6", "effectId": 31, "value": 6},
            {"effect": "Maîtrise Feu : 950", "effectId": 122, "value": 950},
        ],
    }


# ── Stat deltas ──


class TestStatDeltas:
    def test_delta_for_common_stat(self, build_a, build_b):
        result = build_manager.compare_builds(build_a, build_b)
        pv = next(s for s in result["stat_deltas"] if s["effectId"] == 20)
        assert pv["valueA"] == 1200
        assert pv["valueB"] == 1500
        assert pv["delta"] == 300

    def test_delta_zero_when_equal(self, build_a, build_b):
        result = build_manager.compare_builds(build_a, build_b)
        pa = next(s for s in result["stat_deltas"] if s["effectId"] == 31)
        assert pa["delta"] == 0

    def test_stat_only_in_a(self, build_a, build_b):
        """Eau mastery exists only in A → delta is negative (B has 0)."""
        result = build_manager.compare_builds(build_a, build_b)
        eau = next(s for s in result["stat_deltas"] if s["effectId"] == 124)
        assert eau["valueA"] == 800
        assert eau["valueB"] == 0
        assert eau["delta"] == -800

    def test_stat_only_in_b(self, build_a, build_b):
        """Feu mastery exists only in B → delta is positive."""
        result = build_manager.compare_builds(build_a, build_b)
        feu = next(s for s in result["stat_deltas"] if s["effectId"] == 122)
        assert feu["valueA"] == 0
        assert feu["valueB"] == 950
        assert feu["delta"] == 950

    def test_all_effect_ids_covered(self, build_a, build_b):
        result = build_manager.compare_builds(build_a, build_b)
        effect_ids = {s["effectId"] for s in result["stat_deltas"]}
        assert effect_ids == {20, 31, 122, 124, 125}

    def test_effect_label_strips_value(self, build_a, build_b):
        result = build_manager.compare_builds(build_a, build_b)
        pv = next(s for s in result["stat_deltas"] if s["effectId"] == 20)
        assert pv["effect"] == "PV"

    def test_is_malus_false_for_boost(self, build_a, build_b):
        result = build_manager.compare_builds(build_a, build_b)
        pv = next(s for s in result["stat_deltas"] if s["effectId"] == 20)
        assert pv["isMalus"] is False

    def test_is_malus_true_for_deboost(self):
        a = {"name": "A", "items": [], "stats": [
            {"effect": "Deboost : Point de vie (PV) : 100", "effectId": 21, "value": 100},
        ]}
        b = {"name": "B", "items": [], "stats": [
            {"effect": "Deboost : Point de vie (PV) : 50", "effectId": 21, "value": 50},
        ]}
        result = build_manager.compare_builds(a, b)
        pv_minus = next(s for s in result["stat_deltas"] if s["effectId"] == 21)
        assert pv_minus["isMalus"] is True
        assert pv_minus["delta"] == -50

    def test_is_malus_true_for_perte(self):
        a = {"name": "A", "items": [], "stats": [
            {"effect": "Perte : Portée : 2", "effectId": 161, "value": 2},
        ]}
        b = {"name": "B", "items": [], "stats": [
            {"effect": "Perte : Portée : 1", "effectId": 161, "value": 1},
        ]}
        result = build_manager.compare_builds(a, b)
        portee = next(s for s in result["stat_deltas"] if s["effectId"] == 161)
        assert portee["isMalus"] is True
        assert portee["delta"] == -1

    def test_is_malus_false_for_gain(self):
        a = {"name": "A", "items": [], "stats": [
            {"effect": "Gain : Résistance Feu : 50", "effectId": 82, "value": 50},
        ]}
        b = {"name": "B", "items": [], "stats": [
            {"effect": "Gain : Résistance Feu : 70", "effectId": 82, "value": 70},
        ]}
        result = build_manager.compare_builds(a, b)
        res = next(s for s in result["stat_deltas"] if s["effectId"] == 82)
        assert res["isMalus"] is False


# ── Item differences ──


class TestItemDiffs:
    def test_common_items(self, build_a, build_b):
        result = build_manager.compare_builds(build_a, build_b)
        common_ids = {i["id"] for i in result["items_common"]}
        assert common_ids == {1}

    def test_items_removed(self, build_a, build_b):
        """Items in A but not in B."""
        result = build_manager.compare_builds(build_a, build_b)
        removed_ids = {i["id"] for i in result["items_removed"]}
        assert removed_ids == {2, 3}

    def test_items_added(self, build_a, build_b):
        """Items in B but not in A."""
        result = build_manager.compare_builds(build_a, build_b)
        added_ids = {i["id"] for i in result["items_added"]}
        assert added_ids == {4, 5}

    def test_item_names_preserved(self, build_a, build_b):
        result = build_manager.compare_builds(build_a, build_b)
        added_names = {i["name"] for i in result["items_added"]}
        assert "Plastron B" in added_names
        assert "Anneau B" in added_names


# ── Build names ──


class TestBuildNames:
    def test_names_from_builds(self, build_a, build_b):
        result = build_manager.compare_builds(build_a, build_b)
        assert result["name_a"] == "Build Eau/Air"
        assert result["name_b"] == "Build Feu"


# ── Edge cases ──


class TestEdgeCases:
    def test_identical_builds(self, build_a):
        result = build_manager.compare_builds(build_a, build_a)
        for s in result["stat_deltas"]:
            assert s["delta"] == 0
        assert len(result["items_added"]) == 0
        assert len(result["items_removed"]) == 0
        assert len(result["items_common"]) == 3

    def test_empty_stats(self):
        a = {"name": "Empty A", "items": [{"id": 1, "name": "X"}], "stats": []}
        b = {"name": "Empty B", "items": [{"id": 2, "name": "Y"}], "stats": []}
        result = build_manager.compare_builds(a, b)
        assert result["stat_deltas"] == []
        assert len(result["items_added"]) == 1
        assert len(result["items_removed"]) == 1

    def test_no_items(self):
        a = {"name": "A", "items": [], "stats": [{"effect": "PV : 100", "effectId": 20, "value": 100}]}
        b = {"name": "B", "items": [], "stats": [{"effect": "PV : 200", "effectId": 20, "value": 200}]}
        result = build_manager.compare_builds(a, b)
        assert result["stat_deltas"][0]["delta"] == 100
        assert result["items_common"] == []

    def test_missing_stats_key(self):
        a = {"name": "A", "items": []}
        b = {"name": "B", "items": []}
        result = build_manager.compare_builds(a, b)
        assert result["stat_deltas"] == []

    def test_full_roundtrip_with_file(self, tmp_path, build_a, build_b):
        """Save two builds, load them, compare."""
        path = str(tmp_path / "builds.json")
        ea = build_manager.save_build("Build A", build_a["items"], stats=build_a["stats"], path=path)
        eb = build_manager.save_build("Build B", build_b["items"], stats=build_b["stats"], path=path)

        loaded_a = build_manager.get_build(ea["id"], path=path)
        loaded_b = build_manager.get_build(eb["id"], path=path)

        result = build_manager.compare_builds(loaded_a, loaded_b)
        pv = next(s for s in result["stat_deltas"] if s["effectId"] == 20)
        assert pv["delta"] == 300
