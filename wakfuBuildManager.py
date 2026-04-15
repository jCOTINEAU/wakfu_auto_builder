# This Python file uses the following encoding: utf-8
"""QML-exposed model for managing saved builds."""

import json
from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot, Signal, Qt, QAbstractListModel, QModelIndex, QByteArray, QObject

import settings
from settings import simpleActionEnum, paramsActionEnum
from solver import getEquipEffectValue, getEquipEffectValueWithParams
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

    @Slot(str, str, str, str)
    def saveCurrent(self, name, constraints_json, excluded_json, profile_id):
        """Save the current optimization result with constraint snapshot."""
        items = []
        for entry in settings.OPTIMIZED_ITEM_LIST:
            items.append({"id": entry["id"], "name": entry["name"]})

        try:
            constraints = json.loads(constraints_json)
        except (json.JSONDecodeError, ValueError, TypeError):
            constraints = {}

        try:
            excluded = json.loads(excluded_json)
        except (json.JSONDecodeError, ValueError, TypeError):
            excluded = []

        stats = self._snapshot_stats()

        build_manager.save_build(
            name=name,
            items=items,
            constraints=constraints,
            stats=stats,
            excluded_items=excluded,
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
        settings.OPTIMIZED_ITEM_LIST = build.get("items", [])
        constraints_json = json.dumps(build.get("constraints", {}))
        self._last_loaded_excluded = build.get("excluded_items", [])
        self._last_loaded_profile_id = build.get("profile_id", "")
        self.loadSuccess.emit(constraints_json)

    @Slot(result=str)
    def getLastLoadedExcludedJson(self):
        """Return excluded items from the last loaded build as JSON."""
        return json.dumps(self._last_loaded_excluded)

    @Slot(result=str)
    def getLastLoadedProfileId(self):
        """Return the profile ID from the last loaded build."""
        return self._last_loaded_profile_id

    @Slot(str, str, str, str)
    def overwriteCurrent(self, build_id, constraints_json, excluded_json, profile_id):
        """Overwrite an existing build with the current optimization result."""
        items = []
        for entry in settings.OPTIMIZED_ITEM_LIST:
            items.append({"id": entry["id"], "name": entry["name"]})

        try:
            constraints = json.loads(constraints_json)
        except (json.JSONDecodeError, ValueError, TypeError):
            constraints = {}

        try:
            excluded = json.loads(excluded_json)
        except (json.JSONDecodeError, ValueError, TypeError):
            excluded = []

        stats = self._snapshot_stats()

        build_manager.overwrite_build(
            build_id=build_id,
            items=items,
            constraints=constraints,
            stats=stats,
            excluded_items=excluded,
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
        stat_list = []
        for data in simpleActionEnum:
            value = 0
            for item in settings.OPTIMIZED_ITEM_LIST:
                item_data = settings.ITEMS_DATA.get(item["id"])
                if item_data:
                    value += getEquipEffectValue(item_data, data.value)
            if value != 0:
                desc = settings.ACTION_DATA.get(data.value, {})
                effect_text = desc.get("definition", {}).get("effect", f"Action {data.value}")
                stat_list.append({
                    "effect": f"{effect_text} : {value}",
                    "effectId": data.value,
                    "value": value,
                })

        for data in paramsActionEnum:
            value = 0
            nb_elem = 0
            for item in settings.OPTIMIZED_ITEM_LIST:
                item_data = settings.ITEMS_DATA.get(item["id"])
                if item_data:
                    temp = getEquipEffectValueWithParams(item_data, data.value)
                    value += temp
                    if temp != 0:
                        nb_elem = item_data["definition"]["equipEffects"][data.value]["effect"]["definition"]["params"][2]
            if value != 0:
                desc = settings.ACTION_DATA.get(data.value, {})
                effect_text = desc.get("definition", {}).get("effect", f"Action {data.value}")
                stat_list.append({
                    "effect": f"{effect_text} : {value} on {nb_elem} element",
                    "effectId": data.value,
                    "value": value,
                })

        return stat_list
