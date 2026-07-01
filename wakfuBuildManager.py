# This Python file uses the following encoding: utf-8
"""QML-exposed model for managing saved builds."""

import json
from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot, Signal, Qt, QAbstractListModel, QModelIndex, QByteArray, QObject

import settings
from wakutils import compute_stat_summary
import build_manager


QML_IMPORT_NAME = "WakfuBuildManager"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class WakfuBuildManager(QAbstractListModel):
    """List model that exposes saved builds and provides save/load/delete slots."""

    buildIdRole = Qt.UserRole + 1
    buildNameRole = Qt.UserRole + 2
    buildDateRole = Qt.UserRole + 3
    buildItemCountRole = Qt.UserRole + 4

    saveSuccess = Signal()
    loadSuccess = Signal(str)  # emits constraint JSON for the caller to apply
    deleteSuccess = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._builds = build_manager.list_builds()
        self._last_loaded_excluded = []
        self._last_loaded_forced = []
        self._last_loaded_profile_id = ""

    # ── QAbstractListModel interface ──

    def rowCount(self, parent=QModelIndex()):
        return len(self._builds)

    def roleNames(self):
        default = super().roleNames()
        default[self.buildIdRole] = QByteArray(b"buildId")
        default[self.buildNameRole] = QByteArray(b"buildName")
        default[self.buildDateRole] = QByteArray(b"buildDate")
        default[self.buildItemCountRole] = QByteArray(b"buildItemCount")
        return default

    def data(self, index, role: int):
        if not self._builds or not index.isValid():
            return None
        build = self._builds[index.row()]
        if role == self.buildIdRole:
            return build.get("id", "")
        if role == self.buildNameRole:
            return build.get("name", "")
        if role == self.buildDateRole:
            raw = build.get("created_at", "")
            return raw[:16].replace("T", " ") if raw else ""
        if role == self.buildItemCountRole:
            return len(build.get("items", []))
        return None

    # ── Slots callable from QML ──

    @Slot()
    def reload(self):
        """Refresh the build list from disk."""
        self.beginResetModel()
        self._builds = build_manager.list_builds()
        self.endResetModel()

    def _parse_save_args(self, constraints_json, excluded_json, forced_json):
        """Parse the 3 JSON payloads and gather the current items + stats.

        Returns (items, constraints, excluded, forced, stats).
        Malformed JSON falls back to empty defaults ({}, [], []).
        """
        def _load(s, fallback):
            try:
                return json.loads(s)
            except (json.JSONDecodeError, ValueError, TypeError):
                return fallback
        return (
            list(settings.OPTIMIZED_ITEM_LIST),
            _load(constraints_json, {}),
            _load(excluded_json, []),
            _load(forced_json, []),
            self._snapshot_stats(),
        )

    @Slot(str, str, str, str, str)
    def saveCurrent(self, name, constraints_json, excluded_json, forced_json, profile_id):
        """Save the current optimization result with constraint snapshot."""
        items, constraints, excluded, forced, stats = self._parse_save_args(
            constraints_json, excluded_json, forced_json)

        build_manager.save_build(
            name=name,
            items=items,
            constraints=constraints,
            stats=stats,
            excluded_items=excluded,
            forced_items=forced,
            profile_id=profile_id,
        )
        self.reload()
        self.saveSuccess.emit()

    @Slot(str)
    def loadBuild(self, build_id):
        """Load a saved build into the optimized item list and emit constraints."""
        build = build_manager.get_build(build_id)
        if build is None:
            return
        # Copy to detach from the build dict returned by _load_file.
        settings.OPTIMIZED_ITEM_LIST = list(build.get("items", []))

        constraints_json = json.dumps(build.get("constraints", {}))
        self._last_loaded_excluded = build.get("excluded_items", [])
        self._last_loaded_forced = build.get("forced_items", [])
        self._last_loaded_profile_id = build.get("profile_id", "")
        self.loadSuccess.emit(constraints_json)

    @Slot(result=str)
    def getLastLoadedExcludedJson(self):
        """Return excluded items from the last loaded build as JSON."""
        return json.dumps(self._last_loaded_excluded)

    @Slot(result=str)
    def getLastLoadedForcedJson(self):
        """Return forced items from the last loaded build as JSON."""
        return json.dumps(self._last_loaded_forced)

    @Slot(result=str)
    def getLastLoadedProfileId(self):
        """Return the profile ID from the last loaded build."""
        return self._last_loaded_profile_id

    @Slot(str, str, str, str, str)
    def overwriteCurrent(self, build_id, constraints_json, excluded_json, forced_json, profile_id):
        """Overwrite an existing build with the current optimization result."""
        items, constraints, excluded, forced, stats = self._parse_save_args(
            constraints_json, excluded_json, forced_json)

        build_manager.overwrite_build(
            build_id=build_id,
            items=items,
            constraints=constraints,
            stats=stats,
            excluded_items=excluded,
            forced_items=forced,
            profile_id=profile_id,
        )
        self.reload()
        self.saveSuccess.emit()

    @Slot(str)
    def deleteBuild(self, build_id):
        """Delete a saved build."""
        build_manager.delete_build(build_id)
        self.reload()
        self.deleteSuccess.emit()

    @Slot(result=int)
    def count(self):
        """Return the number of saved builds."""
        return len(self._builds)

    @Slot(int, result=str)
    def buildIdAt(self, index):
        """Return the build id at the given list index."""
        if 0 <= index < len(self._builds):
            return self._builds[index].get("id", "")
        return ""

    @Slot(int, result=str)
    def buildNameAt(self, index):
        """Return the build name at the given list index."""
        if 0 <= index < len(self._builds):
            return self._builds[index].get("name", "")
        return ""

    # ── Internal helpers ──

    def _snapshot_stats(self):
        """Compute stat summary for the current optimized set."""
        return compute_stat_summary(settings.OPTIMIZED_ITEM_LIST)
