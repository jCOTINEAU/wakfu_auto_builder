# This Python file uses the following encoding: utf-8
from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot,QObject,Signal,Qt,QAbstractListModel,QModelIndex,QByteArray

import settings
from wakutils import SLOT_ORDER, slot_of, gfx_id_of, name_of, rarity_of


QML_IMPORT_NAME = "WakfuItemList"
QML_IMPORT_MAJOR_VERSION = 1


def _sort_key(item_id):
    slot = slot_of(item_id)
    try:
        return (SLOT_ORDER.index(slot), item_id)
    except ValueError:
        return (len(SLOT_ORDER), item_id)


@QmlElement
class WakfuItemList(QAbstractListModel):

    wakItemIdRole = Qt.UserRole + 1
    wakItemNameRole = Qt.UserRole + 2
    wakItemSlotRole = Qt.UserRole + 3
    wakItemGfxIdRole = Qt.UserRole + 4
    wakItemRarityRole = Qt.UserRole + 5

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.itemList = self._sorted(settings.OPTIMIZED_ITEM_LIST)

    @staticmethod
    def _sorted(ids):
        return sorted(ids, key=_sort_key)

    def rowCount(self, parent=QModelIndex()):
        return len(self.itemList)

    def roleNames(self):
        default = super().roleNames()
        default[self.wakItemIdRole] = QByteArray(b"itemId")
        default[self.wakItemNameRole] = QByteArray(b"itemName")
        default[self.wakItemSlotRole] = QByteArray(b"itemSlot")
        default[self.wakItemGfxIdRole] = QByteArray(b"itemGfxId")
        default[self.wakItemRarityRole] = QByteArray(b"itemRarity")
        return default

    def data(self, index, role: int):
        if not self.itemList or not index.isValid():
            return None
        item_id = self.itemList[index.row()]
        if role == self.wakItemIdRole:
            return item_id
        if role == self.wakItemNameRole:
            return name_of(item_id)
        if role == self.wakItemSlotRole:
            return slot_of(item_id)
        if role == self.wakItemGfxIdRole:
            return gfx_id_of(item_id)
        if role == self.wakItemRarityRole:
            return rarity_of(item_id)
        return None

    @Slot()
    def reload(self):
        self.beginResetModel()
        self.itemList = self._sorted(settings.OPTIMIZED_ITEM_LIST)
        self.endResetModel()
