# This Python file uses the following encoding: utf-8
"""QML models for build comparison — stat deltas and item diffs."""

from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot, Signal, Property, Qt, QAbstractListModel, QModelIndex, QByteArray, QObject

import build_manager
from wakutils import (
    SLOT_ORDER,
    SLOT_LABELS_FR,
    slot_of,
    name_of,
    gfx_id_of,
    rarity_of,
)


QML_IMPORT_NAME = "WakfuBuildComparison"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class WakfuBuildComparison(QObject):
    """Orchestrator that holds comparison results and exposes sub-models."""

    comparisonReady = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._stat_model = ComparisonStatModel(self)
        self._slot_row_model = ComparisonSlotRowModel(self)
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
    def itemSlotModel(self):
        return self._slot_row_model

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
        self._slot_row_model.setData(build_a["items"], build_b["items"])
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


def _pair_slot(items_a_slot, items_b_slot):
    """Return list of (idA, idB, status) tuples for a single slot bucket.

    Matches identical items first (marks them 'equal'); pairs the rest
    positionally as 'diff', or 'onlyA' / 'onlyB' when one side has no
    counterpart.
    """
    common = set(items_a_slot) & set(items_b_slot)
    rows = []
    for iid in items_a_slot:
        if iid in common:
            rows.append((iid, iid, "equal"))
    a_left = [i for i in items_a_slot if i not in common]
    b_left = [i for i in items_b_slot if i not in common]
    for i in range(max(len(a_left), len(b_left))):
        a_id = a_left[i] if i < len(a_left) else None
        b_id = b_left[i] if i < len(b_left) else None
        if a_id is not None and b_id is not None:
            rows.append((a_id, b_id, "diff"))
        elif a_id is not None:
            rows.append((a_id, None, "onlyA"))
        else:
            rows.append((None, b_id, "onlyB"))
    return rows


class ComparisonSlotRowModel(QAbstractListModel):
    """One row per equipment slot, showing item A and item B side-by-side."""

    slotRole       = Qt.UserRole + 1
    slotLabelRole  = Qt.UserRole + 2
    itemAIdRole    = Qt.UserRole + 3
    itemANameRole  = Qt.UserRole + 4
    itemAGfxRole   = Qt.UserRole + 5
    itemARarRole   = Qt.UserRole + 6
    itemBIdRole    = Qt.UserRole + 7
    itemBNameRole  = Qt.UserRole + 8
    itemBGfxRole   = Qt.UserRole + 9
    itemBRarRole   = Qt.UserRole + 10
    statusRole     = Qt.UserRole + 11

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._rows = []

    def setData(self, items_a, items_b):
        self.beginResetModel()
        self._rows = []
        for slot in SLOT_ORDER:
            in_a = [i for i in items_a if slot_of(i) == slot]
            in_b = [i for i in items_b if slot_of(i) == slot]
            pairs = _pair_slot(in_a, in_b)
            for i, (a_id, b_id, status) in enumerate(pairs):
                label = SLOT_LABELS_FR.get(slot, slot)
                if len(pairs) > 1:
                    label = f"{label} {i + 1}"
                self._rows.append({
                    "slot": slot,
                    "slotLabel": label,
                    "a_id": a_id,
                    "b_id": b_id,
                    "status": status,
                })
        # Differences first, then equal rows. Stable sort preserves slot order
        # within each group.
        self._rows.sort(key=lambda r: 1 if r["status"] == "equal" else 0)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def roleNames(self):
        default = super().roleNames()
        default[self.slotRole]      = QByteArray(b"slot")
        default[self.slotLabelRole] = QByteArray(b"slotLabel")
        default[self.itemAIdRole]   = QByteArray(b"itemAId")
        default[self.itemANameRole] = QByteArray(b"itemAName")
        default[self.itemAGfxRole]  = QByteArray(b"itemAGfxId")
        default[self.itemARarRole]  = QByteArray(b"itemARarity")
        default[self.itemBIdRole]   = QByteArray(b"itemBId")
        default[self.itemBNameRole] = QByteArray(b"itemBName")
        default[self.itemBGfxRole]  = QByteArray(b"itemBGfxId")
        default[self.itemBRarRole]  = QByteArray(b"itemBRarity")
        default[self.statusRole]    = QByteArray(b"status")
        return default

    def data(self, index, role: int):
        if not self._rows or not index.isValid():
            return None
        row = self._rows[index.row()]
        if role == self.slotRole:      return row["slot"]
        if role == self.slotLabelRole: return row["slotLabel"]
        if role == self.statusRole:    return row["status"]
        # Fields for side A
        if role == self.itemAIdRole:   return row["a_id"] or 0
        if role == self.itemANameRole: return name_of(row["a_id"]) if row["a_id"] else ""
        if role == self.itemAGfxRole:  return gfx_id_of(row["a_id"]) or 0 if row["a_id"] else 0
        if role == self.itemARarRole:  return rarity_of(row["a_id"]) if row["a_id"] else 0
        # Fields for side B
        if role == self.itemBIdRole:   return row["b_id"] or 0
        if role == self.itemBNameRole: return name_of(row["b_id"]) if row["b_id"] else ""
        if role == self.itemBGfxRole:  return gfx_id_of(row["b_id"]) or 0 if row["b_id"] else 0
        if role == self.itemBRarRole:  return rarity_of(row["b_id"]) if row["b_id"] else 0
        return None
