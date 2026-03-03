# This Python file uses the following encoding: utf-8
"""QML-exposed model for managing character stat profiles."""

import json
import threading
from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot, Signal, Qt, QAbstractListModel, QModelIndex, QByteArray

import stat_profile_manager
from stat_profile_manager import DEFAULT_STATS, STAT_LABELS
import zenith_importer


QML_IMPORT_NAME = "WakfuStatProfileManager"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class WakfuStatProfileManager(QAbstractListModel):
    """List model that exposes saved stat profiles and provides CRUD slots."""

    profileIdRole = Qt.UserRole + 1
    profileNameRole = Qt.UserRole + 2
    profileDateRole = Qt.UserRole + 3

    saveSuccess = Signal()
    deleteSuccess = Signal()
    editingStatsChanged = Signal()
    zenithFetchComplete = Signal(str)   # emits result JSON when background fetch finishes

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._profiles = stat_profile_manager.list_profiles()
        self._editing_stats = dict(DEFAULT_STATS)
        self._editing_id = ""
        self._zenith_url = ""

    # ── QAbstractListModel interface ──

    def rowCount(self, parent=QModelIndex()):
        return len(self._profiles)

    def roleNames(self):
        default = super().roleNames()
        default[self.profileIdRole] = QByteArray(b"profileId")
        default[self.profileNameRole] = QByteArray(b"profileName")
        default[self.profileDateRole] = QByteArray(b"profileDate")
        return default

    def data(self, index, role: int):
        if not self._profiles or not index.isValid():
            return None
        profile = self._profiles[index.row()]
        if role == self.profileIdRole:
            return profile.get("id", "")
        if role == self.profileNameRole:
            return profile.get("name", "")
        if role == self.profileDateRole:
            raw = profile.get("created_at", "")
            return raw[:16].replace("T", " ") if raw else ""
        return None

    # ── Slots callable from QML ──

    @Slot()
    def reload(self):
        self.beginResetModel()
        self._profiles = stat_profile_manager.list_profiles()
        self.endResetModel()

    @Slot(result=int)
    def count(self):
        return len(self._profiles)

    @Slot(int, result=str)
    def profileIdAt(self, index):
        if 0 <= index < len(self._profiles):
            return self._profiles[index].get("id", "")
        return ""

    @Slot(int, result=str)
    def profileNameAt(self, index):
        if 0 <= index < len(self._profiles):
            return self._profiles[index].get("name", "")
        return ""

    @Slot(str)
    def saveProfile(self, name):
        """Save a new profile with the current editing stats."""
        stat_profile_manager.save_profile(
            name=name,
            stats=dict(self._editing_stats),
            zenith_url=self._zenith_url,
        )
        self.reload()
        self.saveSuccess.emit()

    @Slot(str)
    def overwriteProfile(self, profile_id):
        """Overwrite an existing profile with the current editing stats."""
        stat_profile_manager.overwrite_profile(
            profile_id=profile_id,
            stats=dict(self._editing_stats),
            zenith_url=self._zenith_url,
        )
        self.reload()
        self.saveSuccess.emit()

    @Slot(str)
    def deleteProfile(self, profile_id):
        stat_profile_manager.delete_profile(profile_id)
        self.reload()
        self.deleteSuccess.emit()

    # ── Editing stats (for the editor form) ──

    @Slot()
    def resetEditing(self):
        """Reset editing stats to defaults (for new profile)."""
        self._editing_stats = dict(DEFAULT_STATS)
        self._editing_id = ""
        self._zenith_url = ""

    @Slot(str)
    def loadForEditing(self, profile_id):
        """Load an existing profile's stats into the editing buffer."""
        profile = stat_profile_manager.get_profile(profile_id)
        if profile:
            self._editing_stats = dict(DEFAULT_STATS)
            for k, v in profile.get("stats", {}).items():
                if k in self._editing_stats:
                    self._editing_stats[k] = v
            self._editing_id = profile_id
            self._zenith_url = profile.get("zenith_url", "")

    @Slot(str, result=int)
    def getEditingStat(self, key):
        return self._editing_stats.get(key, 0)

    @Slot(str, int)
    def setEditingStat(self, key, value):
        if key in self._editing_stats:
            self._editing_stats[key] = value

    @Slot(result=str)
    def getEditingId(self):
        return self._editing_id

    @Slot(result=str)
    def statKeysJson(self):
        """Return JSON array of stat keys in display order."""
        return json.dumps(list(DEFAULT_STATS.keys()))

    @Slot(str, result=str)
    def statLabel(self, key):
        """Return the display label for a stat key."""
        return STAT_LABELS.get(key, key)

    @Slot(str, result=int)
    def statDefault(self, key):
        """Return the default value for a stat key."""
        return DEFAULT_STATS.get(key, 0)

    @Slot(str, result=str)
    def getProfileStatsJson(self, profile_id):
        """Return the stats dict of a profile as a JSON string."""
        profile = stat_profile_manager.get_profile(profile_id)
        if profile:
            return json.dumps(profile.get("stats", {}))
        return "{}"

    # ── Zenith import ──

    @Slot(result=str)
    def getZenithUrl(self):
        return self._zenith_url

    @Slot(str)
    def setZenithUrl(self, url):
        self._zenith_url = url.strip()

    @Slot(str)
    def fetchFromZenith(self, url):
        """Start an async Zenith fetch in a background thread.

        Emits zenithFetchComplete(result_json) when done.
        result_json: { "stats": {...}, "has_equipment": bool, "equipment_count": int, "error": str }
        """
        self._zenith_url = url.strip()
        _url = url  # capture for the closure

        def _worker():
            result = zenith_importer.import_zenith_build(_url)
            self.zenithFetchComplete.emit(json.dumps(result))

        threading.Thread(target=_worker, daemon=True).start()

    @Slot(str)
    def applyZenithStats(self, result_json):
        """Apply the stats dict from a fetchFromZenith result to the editing buffer."""
        try:
            data = json.loads(result_json)
            stats = data.get("stats", {})
            for k, v in stats.items():
                if k in self._editing_stats:
                    self._editing_stats[k] = v
            self.editingStatsChanged.emit()
        except (json.JSONDecodeError, ValueError):
            pass
