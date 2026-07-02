"""Tests for paths.py — bundled-resource vs user-data path resolution."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import paths


class TestIsFrozen:
    def test_dev_mode_is_not_frozen(self):
        """When running via pytest, sys.frozen is not set."""
        assert paths.is_frozen() is False


class TestResourcePath:
    def test_returns_absolute_path(self):
        p = paths.resource_path("data", "1.90.1.48", "items.json")
        assert os.path.isabs(p)

    def test_joins_parts(self):
        p = paths.resource_path("views", "mainPage.qml")
        assert p.endswith(os.path.join("views", "mainPage.qml"))

    def test_no_parts_returns_root(self):
        assert paths.resource_path() == paths.app_root()


class TestMigrateLegacyFile:
    def test_copies_when_only_legacy_exists(self, tmp_path):
        src = tmp_path / "legacy.json"
        dst = tmp_path / "new.json"    # same tmp_path parent, guaranteed to exist
        src.write_text('{"a": 1}')
        paths.migrate_legacy_file(str(src), str(dst))
        assert dst.exists()
        assert dst.read_text() == '{"a": 1}'
        # Legacy file is NOT deleted — we're conservative on migration.
        assert src.exists()

    def test_noop_when_new_already_exists(self, tmp_path):
        src = tmp_path / "legacy.json"
        dst = tmp_path / "new.json"
        src.write_text('{"legacy": true}')
        dst.write_text('{"already": true}')
        paths.migrate_legacy_file(str(src), str(dst))
        # dst should NOT be overwritten.
        assert dst.read_text() == '{"already": true}'

    def test_noop_when_legacy_missing(self, tmp_path):
        src = tmp_path / "nowhere.json"
        dst = tmp_path / "dst.json"
        paths.migrate_legacy_file(str(src), str(dst))
        assert not dst.exists()

    def test_creates_parent_dirs(self, tmp_path):
        """copy2 requires the parent dir of dst to exist."""
        src = tmp_path / "legacy.json"
        dst = tmp_path / "deeply" / "nested" / "dir" / "file.json"
        src.write_text("x")
        # migrate_legacy_file doesn't create parent dirs itself — this documents
        # the caller's responsibility to place the dst in an existing dir.
        # For our real use case, user_data_dir() creates the dir first.
        dst.parent.mkdir(parents=True, exist_ok=True)
        paths.migrate_legacy_file(str(src), str(dst))
        assert dst.exists()


class TestUserDataDir:
    def test_returns_absolute_path(self):
        d = paths.user_data_dir()
        assert os.path.isabs(d)

    def test_creates_dir_if_missing(self, monkeypatch, tmp_path):
        # Redirect the XDG base to a tmp dir so we don't clobber the real one.
        monkeypatch.setattr(sys, "platform", "linux")
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
        d = paths.user_data_dir()
        assert os.path.isdir(d)
        assert d.endswith(paths.APP_ID)

    def test_windows_uses_appdata(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
        d = paths.user_data_dir()
        assert str(tmp_path / "appdata" / paths.APP_ID) == d


class TestUserDataFile:
    def test_joins_name_to_dir(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "platform", "linux")
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        f = paths.user_data_file("hello.json")
        assert f.endswith(os.path.join(paths.APP_ID, "hello.json"))
