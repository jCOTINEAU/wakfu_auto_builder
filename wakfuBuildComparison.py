# This Python file uses the following encoding: utf-8
"""QML models for build comparison — stat deltas and item diffs."""

from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot, Signal, Property, Qt, QAbstractListModel, QModelIndex, QByteArray, QObject

import build_manager


QML_IMPORT_NAME = "WakfuBuildComparison"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class WakfuBuildComparison(QObject):
    """Orchestrator that holds comparison results and exposes sub-models."""

    comparisonReady = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._stat_model = ComparisonStatModel(self)
        self._item_diff_model = ComparisonItemDiffModel(self)
        self._name_a = ""
        self._name_b = ""

    # ── Properties for QML ──

    nameAChanged = Signal()
    nameBChanged = Signal()

    @Property(str, notify=nameAChanged)
    def nameA(self):
        return self._name_a

    @Property(str, notify=nameBChanged)
    def nameB(self):
        return self._name_b

    @Slot(result=QObject)
    def statModel(self):
        return self._stat_model

    @Slot(result=QObject)
    def itemDiffModel(self):
        return self._item_diff_model

    @Slot(str, str)
    def compareByIds(self, id_a, id_b):
        """Compare two saved builds by their ids."""
        build_a = build_manager.get_build(id_a)
        build_b = build_manager.get_build(id_b)
        if build_a is None or build_b is None:
            return
        result = build_manager.compare_builds(build_a, build_b)

        self._name_a = result["name_a"]
        self._name_b = result["name_b"]
        self.nameAChanged.emit()
        self.nameBChanged.emit()

        self._stat_model.setData(result["stat_deltas"])
        self._item_diff_model.setData(
            result["items_added"],
            result["items_removed"],
            result["items_common"],
        )
        self.comparisonReady.emit()


class ComparisonStatModel(QAbstractListModel):
    """List model for stat deltas between two builds."""

    effectRole = Qt.UserRole + 1
    valueARole = Qt.UserRole + 2
    valueBRole = Qt.UserRole + 3
    deltaRole = Qt.UserRole + 4
    isMalusRole = Qt.UserRole + 5

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._rows = []

    def setData(self, stat_deltas):
        self.beginResetModel()
        self._rows = stat_deltas
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def roleNames(self):
        default = super().roleNames()
        default[self.effectRole] = QByteArray(b"effect")
        default[self.valueARole] = QByteArray(b"valueA")
        default[self.valueBRole] = QByteArray(b"valueB")
        default[self.deltaRole] = QByteArray(b"delta")
        default[self.isMalusRole] = QByteArray(b"isMalus")
        return default

    def data(self, index, role: int):
        if not self._rows or not index.isValid():
            return None
        row = self._rows[index.row()]
        if role == self.effectRole:
            return row.get("effect", "")
        if role == self.valueARole:
            return row.get("valueA", 0)
        if role == self.valueBRole:
            return row.get("valueB", 0)
        if role == self.deltaRole:
            return row.get("delta", 0)
        if role == self.isMalusRole:
            return row.get("isMalus", False)
        return None


class ComparisonItemDiffModel(QAbstractListModel):
    """List model for item differences: added (+), removed (-), common (=)."""

    itemNameRole = Qt.UserRole + 1
    diffTypeRole = Qt.UserRole + 2

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._rows = []

    def setData(self, added, removed, common):
        self.beginResetModel()
        self._rows = []
        for item in removed:
            self._rows.append({"name": item["name"], "type": "removed"})
        for item in added:
            self._rows.append({"name": item["name"], "type": "added"})
        for item in common:
            self._rows.append({"name": item["name"], "type": "common"})
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def roleNames(self):
        default = super().roleNames()
        default[self.itemNameRole] = QByteArray(b"itemName")
        default[self.diffTypeRole] = QByteArray(b"diffType")
        return default

    def data(self, index, role: int):
        if not self._rows or not index.isValid():
            return None
        row = self._rows[index.row()]
        if role == self.itemNameRole:
            return row.get("name", "")
        if role == self.diffTypeRole:
            return row.get("type", "")
        return None
