# This Python file uses the following encoding: utf-8
"""QML-exposed item search model — used by the item filter dialog."""

import json
import unicodedata

from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot, Signal, Property, Qt, QAbstractListModel, QModelIndex, QByteArray

import settings
from wakutils import SLOT_ORDER, SLOT_LABELS_FR, slot_of, gfx_id_of, rarity_of


QML_IMPORT_NAME = "WakfuItemSearch"
QML_IMPORT_MAJOR_VERSION = 1

MAX_RESULTS = 30


def _norm(s):
    """Lowercase, accent-stripped for case/accent-insensitive matching."""
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()


@QmlElement
class WakfuItemSearch(QAbstractListModel):
    """Search items by (fuzzy) name and optional slot filter."""

    itemIdRole     = Qt.UserRole + 1
    itemNameRole   = Qt.UserRole + 2
    itemGfxIdRole  = Qt.UserRole + 3
    itemRarityRole = Qt.UserRole + 4
    itemSlotRole   = Qt.UserRole + 5
    itemLevelRole  = Qt.UserRole + 6

    totalMatchesChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._rows = []
        self._total_matches = 0

    @Property(int, notify=totalMatchesChanged)
    def totalMatches(self):
        return self._total_matches

    @Property(int, notify=totalMatchesChanged)
    def maxResults(self):
        return MAX_RESULTS

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def roleNames(self):
        default = super().roleNames()
        default[self.itemIdRole]     = QByteArray(b"itemId")
        default[self.itemNameRole]   = QByteArray(b"itemName")
        default[self.itemGfxIdRole]  = QByteArray(b"itemGfxId")
        default[self.itemRarityRole] = QByteArray(b"itemRarity")
        default[self.itemSlotRole]   = QByteArray(b"itemSlot")
        default[self.itemLevelRole]  = QByteArray(b"itemLevel")
        return default

    def data(self, index, role: int):
        if not self._rows or not index.isValid():
            return None
        row = self._rows[index.row()]
        if role == self.itemIdRole:     return row["id"]
        if role == self.itemNameRole:   return row["name"]
        if role == self.itemGfxIdRole:  return row["gfxId"] or 0
        if role == self.itemRarityRole: return row["rarity"]
        if role == self.itemSlotRole:   return row["slot"]
        if role == self.itemLevelRole:  return row["level"]
        return None

    @Slot(str, str)
    def setQuery(self, query, slot_filter=""):
        """Refresh matches for the given query and optional slot filter.

        Slot filter is a SLOT_ORDER key (HEAD, RING, …) or "" for any slot.
        Empty query with empty slot filter clears the results.
        """
        q = _norm(query).strip()
        self.beginResetModel()
        self._rows = []

        if not q and not slot_filter:
            self._total_matches = 0
            self.totalMatchesChanged.emit()
            self.endResetModel()
            return

        matches = []
        for iid, item in settings.ITEMS_DATA.items():
            if item["definition"]["item"].get("shardsParameters", 0) != 0:
                continue
            slot = slot_of(iid)
            if slot == "OTHER":
                continue
            if slot_filter and slot != slot_filter:
                continue

            name = item["title"].get("fr", "")
            name_norm = _norm(name)
            if q and q not in name_norm:
                continue

            matches.append({
                "id":     iid,
                "name":   name,
                "gfxId":  gfx_id_of(iid),
                "rarity": rarity_of(iid),
                "slot":   slot,
                "level":  item["definition"]["item"]["level"],
                # sort key: prefix match ranks highest, then by level desc
                "_prefix": 0 if (q and name_norm.startswith(q)) else 1,
            })

        matches.sort(key=lambda r: (r["_prefix"], -r["level"], r["name"]))
        self._total_matches = len(matches)
        self._rows = matches[:MAX_RESULTS]
        self.totalMatchesChanged.emit()
        self.endResetModel()

    @Slot()
    def clear(self):
        self.beginResetModel()
        self._rows = []
        self._total_matches = 0
        self.totalMatchesChanged.emit()
        self.endResetModel()

    @Slot(result=str)
    def slotOptionsJson(self):
        """Return JSON [{key,label}] for a ComboBox: "any" first, then SLOT_ORDER."""
        options = [{"key": "", "label": "Tous slots"}]
        for slot in SLOT_ORDER:
            options.append({"key": slot, "label": SLOT_LABELS_FR.get(slot, slot)})
        return json.dumps(options, ensure_ascii=False)
