"""Tests for stat_profile_manager.py — save / list / get / delete / overwrite profiles."""

import json
import os
import sys
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import stat_profile_manager
from stat_profile_manager import DEFAULT_STATS


@pytest.fixture
def save_path(tmp_path):
    return str(tmp_path / "test_profiles.json")


# ── save_profile ──


class TestSaveProfile:
    def test_save_creates_file(self, save_path):
        stat_profile_manager.save_profile("Sram 230", path=save_path)
        assert os.path.exists(save_path)

    def test_save_returns_entry_with_id(self, save_path):
        entry = stat_profile_manager.save_profile("Sram 230", path=save_path)
        assert "id" in entry
        assert entry["name"] == "Sram 230"

    def test_save_fills_defaults(self, save_path):
        entry = stat_profile_manager.save_profile("Test", path=save_path)
        assert entry["stats"]["PA"] == 6
        assert entry["stats"]["PM"] == 3
        assert entry["stats"]["PW"] == 6
        assert entry["stats"]["PV"] == 0

    def test_save_with_custom_stats(self, save_path):
        custom = {"PV": 500, "tacle": 30}
        entry = stat_profile_manager.save_profile("Custom", stats=custom, path=save_path)
        assert entry["stats"]["PV"] == 500
        assert entry["stats"]["tacle"] == 30
        assert entry["stats"]["PA"] == 6  # default preserved

    def test_save_ignores_unknown_keys(self, save_path):
        custom = {"PV": 100, "unknown_stat": 999}
        entry = stat_profile_manager.save_profile("Test", stats=custom, path=save_path)
        assert "unknown_stat" not in entry["stats"]
        assert entry["stats"]["PV"] == 100

    def test_save_empty_name_defaults(self, save_path):
        entry = stat_profile_manager.save_profile("  ", path=save_path)
        assert entry["name"] == "Sans nom"

    def test_save_includes_timestamp(self, save_path):
        entry = stat_profile_manager.save_profile("Test", path=save_path)
        assert "created_at" in entry
        assert "T" in entry["created_at"]

    def test_save_appends(self, save_path):
        stat_profile_manager.save_profile("A", path=save_path)
        stat_profile_manager.save_profile("B", path=save_path)
        profiles = stat_profile_manager.list_profiles(path=save_path)
        assert len(profiles) == 2


# ── list_profiles ──


class TestListProfiles:
    def test_list_empty(self, save_path):
        assert stat_profile_manager.list_profiles(path=save_path) == []

    def test_list_newest_first(self, save_path):
        stat_profile_manager.save_profile("Old", path=save_path)
        stat_profile_manager.save_profile("New", path=save_path)
        profiles = stat_profile_manager.list_profiles(path=save_path)
        assert profiles[0]["name"] == "New"

    def test_list_handles_corrupt_file(self, save_path):
        with open(save_path, "w") as f:
            f.write("not json{{{")
        assert stat_profile_manager.list_profiles(path=save_path) == []


# ── get_profile ──


class TestGetProfile:
    def test_get_existing(self, save_path):
        entry = stat_profile_manager.save_profile("Target", path=save_path)
        result = stat_profile_manager.get_profile(entry["id"], path=save_path)
        assert result is not None
        assert result["name"] == "Target"

    def test_get_nonexistent(self, save_path):
        assert stat_profile_manager.get_profile("fake-id", path=save_path) is None


# ── delete_profile ──


class TestDeleteProfile:
    def test_delete_existing(self, save_path):
        entry = stat_profile_manager.save_profile("ToDelete", path=save_path)
        assert stat_profile_manager.delete_profile(entry["id"], path=save_path) is True
        assert stat_profile_manager.list_profiles(path=save_path) == []

    def test_delete_nonexistent(self, save_path):
        stat_profile_manager.save_profile("Keep", path=save_path)
        assert stat_profile_manager.delete_profile("fake", path=save_path) is False
        assert len(stat_profile_manager.list_profiles(path=save_path)) == 1

    def test_delete_preserves_others(self, save_path):
        keep = stat_profile_manager.save_profile("Keep", path=save_path)
        remove = stat_profile_manager.save_profile("Remove", path=save_path)
        stat_profile_manager.delete_profile(remove["id"], path=save_path)
        profiles = stat_profile_manager.list_profiles(path=save_path)
        assert len(profiles) == 1
        assert profiles[0]["id"] == keep["id"]


# ── overwrite_profile ──


class TestOverwriteProfile:
    def test_overwrite_replaces_stats(self, save_path):
        entry = stat_profile_manager.save_profile("Test", stats={"tacle": 10}, path=save_path)
        result = stat_profile_manager.overwrite_profile(
            entry["id"], stats={"tacle": 50, "PV": 1000}, path=save_path
        )
        assert result["stats"]["tacle"] == 50
        assert result["stats"]["PV"] == 1000
        assert result["stats"]["PA"] == 6  # default

    def test_overwrite_keeps_id(self, save_path):
        entry = stat_profile_manager.save_profile("Test", path=save_path)
        result = stat_profile_manager.overwrite_profile(entry["id"], stats={"PV": 99}, path=save_path)
        assert result["id"] == entry["id"]

    def test_overwrite_can_change_name(self, save_path):
        entry = stat_profile_manager.save_profile("Old Name", path=save_path)
        result = stat_profile_manager.overwrite_profile(entry["id"], name="New Name", path=save_path)
        assert result["name"] == "New Name"

    def test_overwrite_keeps_name_if_not_specified(self, save_path):
        entry = stat_profile_manager.save_profile("Keep Name", path=save_path)
        result = stat_profile_manager.overwrite_profile(entry["id"], stats={"PV": 1}, path=save_path)
        assert result["name"] == "Keep Name"

    def test_overwrite_updates_timestamp(self, save_path):
        entry = stat_profile_manager.save_profile("Test", path=save_path)
        old_ts = entry["created_at"]
        time.sleep(0.01)
        result = stat_profile_manager.overwrite_profile(entry["id"], stats={"PV": 1}, path=save_path)
        assert result["created_at"] > old_ts

    def test_overwrite_nonexistent(self, save_path):
        stat_profile_manager.save_profile("Existing", path=save_path)
        result = stat_profile_manager.overwrite_profile("fake-id", stats={"PV": 1}, path=save_path)
        assert result is None

    def test_overwrite_persists(self, save_path):
        entry = stat_profile_manager.save_profile("Test", stats={"tacle": 5}, path=save_path)
        stat_profile_manager.overwrite_profile(entry["id"], stats={"tacle": 99}, path=save_path)
        reloaded = stat_profile_manager.get_profile(entry["id"], path=save_path)
        assert reloaded["stats"]["tacle"] == 99


# ── defaults ──


class TestDefaults:
    def test_all_default_keys_present(self, save_path):
        entry = stat_profile_manager.save_profile("Test", path=save_path)
        for key in DEFAULT_STATS:
            assert key in entry["stats"]

    def test_default_values(self):
        assert DEFAULT_STATS["PA"] == 6
        assert DEFAULT_STATS["PM"] == 3
        assert DEFAULT_STATS["PW"] == 6
        assert DEFAULT_STATS["PV"] == 0
        assert DEFAULT_STATS["tacle"] == 0
