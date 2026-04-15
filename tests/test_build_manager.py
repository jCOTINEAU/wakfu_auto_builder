"""Tests for build_manager.py — save / list / get / delete builds."""

import json
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import build_manager


@pytest.fixture
def save_path(tmp_path):
    """Return a temporary file path for the JSON store."""
    return str(tmp_path / "test_builds.json")


@pytest.fixture
def sample_items():
    """A minimal list of optimized items."""
    return [
        {"id": 2001, "name": "Casque A"},
        {"id": 2002, "name": "Plastron A"},
        {"id": 2013, "name": "Epee A"},
    ]


@pytest.fixture
def sample_stats():
    return [
        {"effect": "PV : 200", "effectId": 20, "value": 200},
        {"effect": "Fire mastery : 150", "effectId": 122, "value": 150},
    ]


# ── save_build ──


class TestSaveBuild:
    def test_save_creates_file(self, save_path, sample_items):
        build_manager.save_build("Mon build", sample_items, path=save_path)
        assert os.path.exists(save_path)

    def test_save_returns_entry_with_id(self, save_path, sample_items):
        entry = build_manager.save_build("Mon build", sample_items, path=save_path)
        assert "id" in entry
        assert entry["name"] == "Mon build"

    def test_save_stores_items(self, save_path, sample_items):
        entry = build_manager.save_build("Mon build", sample_items, path=save_path)
        assert entry["items"] == sample_items

    def test_save_stores_constraints_and_stats(self, save_path, sample_items, sample_stats):
        constraints = {"levelSelector": 230}
        entry = build_manager.save_build(
            "Build complet", sample_items,
            constraints=constraints, stats=sample_stats, path=save_path,
        )
        assert entry["constraints"] == constraints
        assert entry["stats"] == sample_stats

    def test_save_empty_name_defaults(self, save_path, sample_items):
        entry = build_manager.save_build("  ", sample_items, path=save_path)
        assert entry["name"] == "Sans nom"

    def test_save_includes_timestamp(self, save_path, sample_items):
        entry = build_manager.save_build("Test", sample_items, path=save_path)
        assert "created_at" in entry
        assert "T" in entry["created_at"]

    def test_save_appends_to_existing(self, save_path, sample_items):
        build_manager.save_build("Build 1", sample_items, path=save_path)
        build_manager.save_build("Build 2", sample_items, path=save_path)
        builds = build_manager.list_builds(path=save_path)
        assert len(builds) == 2

    def test_save_with_no_constraints_or_stats(self, save_path, sample_items):
        entry = build_manager.save_build("Minimal", sample_items, path=save_path)
        assert entry["constraints"] == {}
        assert entry["stats"] == []


# ── list_builds ──


class TestListBuilds:
    def test_list_empty_when_no_file(self, save_path):
        builds = build_manager.list_builds(path=save_path)
        assert builds == []

    def test_list_returns_all_builds(self, save_path, sample_items):
        build_manager.save_build("A", sample_items, path=save_path)
        build_manager.save_build("B", sample_items, path=save_path)
        build_manager.save_build("C", sample_items, path=save_path)
        builds = build_manager.list_builds(path=save_path)
        assert len(builds) == 3

    def test_list_newest_first(self, save_path, sample_items):
        build_manager.save_build("Old", sample_items, path=save_path)
        build_manager.save_build("New", sample_items, path=save_path)
        builds = build_manager.list_builds(path=save_path)
        assert builds[0]["name"] == "New"
        assert builds[1]["name"] == "Old"

    def test_list_handles_corrupt_file(self, save_path):
        with open(save_path, "w") as f:
            f.write("not valid json {{{")
        builds = build_manager.list_builds(path=save_path)
        assert builds == []

    def test_list_handles_non_list_json(self, save_path):
        with open(save_path, "w") as f:
            json.dump({"not": "a list"}, f)
        builds = build_manager.list_builds(path=save_path)
        assert builds == []


# ── get_build ──


class TestGetBuild:
    def test_get_existing_build(self, save_path, sample_items):
        entry = build_manager.save_build("Target", sample_items, path=save_path)
        result = build_manager.get_build(entry["id"], path=save_path)
        assert result is not None
        assert result["name"] == "Target"
        assert result["items"] == sample_items

    def test_get_nonexistent_build(self, save_path):
        result = build_manager.get_build("nonexistent-id", path=save_path)
        assert result is None

    def test_get_from_multiple_builds(self, save_path, sample_items):
        build_manager.save_build("First", sample_items, path=save_path)
        target = build_manager.save_build("Second", sample_items, path=save_path)
        build_manager.save_build("Third", sample_items, path=save_path)
        result = build_manager.get_build(target["id"], path=save_path)
        assert result["name"] == "Second"


# ── delete_build ──


class TestDeleteBuild:
    def test_delete_existing_build(self, save_path, sample_items):
        entry = build_manager.save_build("ToDelete", sample_items, path=save_path)
        deleted = build_manager.delete_build(entry["id"], path=save_path)
        assert deleted is True
        assert build_manager.list_builds(path=save_path) == []

    def test_delete_nonexistent_build(self, save_path, sample_items):
        build_manager.save_build("Keep", sample_items, path=save_path)
        deleted = build_manager.delete_build("fake-id", path=save_path)
        assert deleted is False
        assert len(build_manager.list_builds(path=save_path)) == 1

    def test_delete_preserves_other_builds(self, save_path, sample_items):
        keep = build_manager.save_build("Keep", sample_items, path=save_path)
        remove = build_manager.save_build("Remove", sample_items, path=save_path)
        build_manager.delete_build(remove["id"], path=save_path)
        builds = build_manager.list_builds(path=save_path)
        assert len(builds) == 1
        assert builds[0]["id"] == keep["id"]

    def test_delete_from_empty_file(self, save_path):
        deleted = build_manager.delete_build("anything", path=save_path)
        assert deleted is False


# ── Edge cases / file handling ──


class TestFileHandling:
    def test_concurrent_saves(self, save_path, sample_items):
        """Multiple rapid saves should all persist."""
        for i in range(10):
            build_manager.save_build(f"Build {i}", sample_items, path=save_path)
        builds = build_manager.list_builds(path=save_path)
        assert len(builds) == 10

    def test_save_with_unicode_name(self, save_path, sample_items):
        entry = build_manager.save_build("Éclipse de feu 🔥", sample_items, path=save_path)
        assert entry["name"] == "Éclipse de feu 🔥"
        reloaded = build_manager.get_build(entry["id"], path=save_path)
        assert reloaded["name"] == "Éclipse de feu 🔥"

    def test_file_is_valid_json(self, save_path, sample_items):
        build_manager.save_build("Test", sample_items, path=save_path)
        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 1

    def test_unique_ids(self, save_path, sample_items):
        ids = set()
        for _ in range(20):
            entry = build_manager.save_build("Same name", sample_items, path=save_path)
            ids.add(entry["id"])
        assert len(ids) == 20


# ── overwrite_build ──


class TestOverwriteBuild:
    def test_overwrite_replaces_items_and_stats(self, save_path, sample_items, sample_stats):
        entry = build_manager.save_build(
            "Original", sample_items,
            constraints={"level": 200}, stats=sample_stats, path=save_path,
        )
        new_items = [{"id": 9999, "name": "Nouvel Item"}]
        new_stats = [{"effect": "PM : 3", "effectId": 41, "value": 3}]
        new_constraints = {"level": 100}

        result = build_manager.overwrite_build(
            entry["id"], new_items,
            constraints=new_constraints, stats=new_stats, path=save_path,
        )

        assert result is not None
        assert result["items"] == new_items
        assert result["stats"] == new_stats
        assert result["constraints"] == new_constraints

    def test_overwrite_keeps_id_and_name(self, save_path, sample_items):
        entry = build_manager.save_build("Mon Build", sample_items, path=save_path)
        original_id = entry["id"]
        original_name = entry["name"]

        new_items = [{"id": 42, "name": "Item X"}]
        result = build_manager.overwrite_build(original_id, new_items, path=save_path)

        assert result["id"] == original_id
        assert result["name"] == original_name

    def test_overwrite_updates_timestamp(self, save_path, sample_items):
        entry = build_manager.save_build("Build", sample_items, path=save_path)
        old_ts = entry["created_at"]

        import time
        time.sleep(0.01)

        result = build_manager.overwrite_build(
            entry["id"], sample_items, path=save_path,
        )
        assert result["created_at"] > old_ts

    def test_overwrite_nonexistent_returns_none(self, save_path, sample_items):
        build_manager.save_build("Existing", sample_items, path=save_path)
        result = build_manager.overwrite_build(
            "fake-id-does-not-exist", sample_items, path=save_path,
        )
        assert result is None

    def test_overwrite_persists_to_disk(self, save_path, sample_items):
        entry = build_manager.save_build("Persist", sample_items, path=save_path)
        new_items = [{"id": 7, "name": "Dague"}]
        build_manager.overwrite_build(entry["id"], new_items, path=save_path)

        reloaded = build_manager.get_build(entry["id"], path=save_path)
        assert reloaded["items"] == new_items
        assert reloaded["name"] == "Persist"

    def test_overwrite_does_not_affect_other_builds(self, save_path, sample_items):
        keep = build_manager.save_build("Keep", sample_items, path=save_path)
        target = build_manager.save_build("Target", sample_items, path=save_path)

        new_items = [{"id": 1, "name": "Changed"}]
        build_manager.overwrite_build(target["id"], new_items, path=save_path)

        kept = build_manager.get_build(keep["id"], path=save_path)
        assert kept["items"] == sample_items


# ── excluded_items ──


class TestExcludedItems:
    def test_save_stores_excluded_items(self, save_path, sample_items):
        excluded = [100, 200, 300]
        entry = build_manager.save_build(
            "With exclusions", sample_items,
            excluded_items=excluded, path=save_path,
        )
        assert entry["excluded_items"] == excluded

    def test_save_defaults_to_empty_excluded(self, save_path, sample_items):
        entry = build_manager.save_build("No exclusions", sample_items, path=save_path)
        assert entry["excluded_items"] == []

    def test_get_build_returns_excluded_items(self, save_path, sample_items):
        excluded = [42, 99]
        entry = build_manager.save_build(
            "Test", sample_items,
            excluded_items=excluded, path=save_path,
        )
        reloaded = build_manager.get_build(entry["id"], path=save_path)
        assert reloaded["excluded_items"] == excluded

    def test_overwrite_replaces_excluded_items(self, save_path, sample_items):
        entry = build_manager.save_build(
            "Original", sample_items,
            excluded_items=[10, 20], path=save_path,
        )
        new_excluded = [30, 40, 50]
        result = build_manager.overwrite_build(
            entry["id"], sample_items,
            excluded_items=new_excluded, path=save_path,
        )
        assert result["excluded_items"] == new_excluded

    def test_overwrite_clears_excluded_when_none(self, save_path, sample_items):
        entry = build_manager.save_build(
            "Had exclusions", sample_items,
            excluded_items=[1, 2, 3], path=save_path,
        )
        result = build_manager.overwrite_build(
            entry["id"], sample_items, path=save_path,
        )
        assert result["excluded_items"] == []

    def test_excluded_items_persist_across_reload(self, save_path, sample_items):
        excluded = [555, 666]
        entry = build_manager.save_build(
            "Persist test", sample_items,
            excluded_items=excluded, path=save_path,
        )
        builds = build_manager.list_builds(path=save_path)
        found = next(b for b in builds if b["id"] == entry["id"])
        assert found["excluded_items"] == excluded


# ── profile_id ──


class TestProfileId:
    def test_save_stores_profile_id(self, save_path, sample_items):
        entry = build_manager.save_build(
            "With profile", sample_items,
            profile_id="prof-abc-123", path=save_path,
        )
        assert entry["profile_id"] == "prof-abc-123"

    def test_save_defaults_to_empty_profile_id(self, save_path, sample_items):
        entry = build_manager.save_build("No profile", sample_items, path=save_path)
        assert entry["profile_id"] == ""

    def test_get_build_returns_profile_id(self, save_path, sample_items):
        entry = build_manager.save_build(
            "Test", sample_items,
            profile_id="some-id", path=save_path,
        )
        reloaded = build_manager.get_build(entry["id"], path=save_path)
        assert reloaded["profile_id"] == "some-id"

    def test_overwrite_replaces_profile_id(self, save_path, sample_items):
        entry = build_manager.save_build(
            "Original", sample_items,
            profile_id="old-prof", path=save_path,
        )
        result = build_manager.overwrite_build(
            entry["id"], sample_items,
            profile_id="new-prof", path=save_path,
        )
        assert result["profile_id"] == "new-prof"

    def test_overwrite_clears_profile_when_empty(self, save_path, sample_items):
        entry = build_manager.save_build(
            "Had profile", sample_items,
            profile_id="old-prof", path=save_path,
        )
        result = build_manager.overwrite_build(
            entry["id"], sample_items, path=save_path,
        )
        assert result["profile_id"] == ""

    def test_profile_id_persists_across_reload(self, save_path, sample_items):
        entry = build_manager.save_build(
            "Persist", sample_items,
            profile_id="persist-prof", path=save_path,
        )
        builds = build_manager.list_builds(path=save_path)
        found = next(b for b in builds if b["id"] == entry["id"])
        assert found["profile_id"] == "persist-prof"

    def test_full_build_with_all_fields(self, save_path, sample_items, sample_stats):
        """Integration test: save a build with all fields and verify on reload."""
        entry = build_manager.save_build(
            "Full build", sample_items,
            constraints={"levelSelector": 200},
            stats=sample_stats,
            excluded_items=[42, 99],
            profile_id="full-prof-id",
            path=save_path,
        )
        reloaded = build_manager.get_build(entry["id"], path=save_path)
        assert reloaded["name"] == "Full build"
        assert reloaded["items"] == sample_items
        assert reloaded["constraints"] == {"levelSelector": 200}
        assert reloaded["stats"] == sample_stats
        assert reloaded["excluded_items"] == [42, 99]
        assert reloaded["profile_id"] == "full-prof-id"
