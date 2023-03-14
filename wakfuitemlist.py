# This Python file uses the following encoding: utf-8
from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot,QObject,Signal,Qt,QAbstractListModel,QModelIndex,QByteArray

import settings


QML_IMPORT_NAME = "WakfuItemList"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class WakfuItemList(QAbstractListModel):

    wakItemIdRole = Qt.UserRole + 1
    wakItemNameRole = Qt.UserRole + 2

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.itemList = settings.OPTIMIZED_ITEM_LIST

    def rowCount(self, parent=QModelIndex()):
        return len(self.itemList)

    def roleNames(self):
        default = super().roleNames()
        default[self.wakItemIdRole] = QByteArray(b"itemId")
        default[self.wakItemNameRole] = QByteArray(b"itemName")
        return default

    def data(self, index, role: int):
        if not self.itemList:
            ret = None
        elif not index.isValid():
            ret = None
        elif role == self.wakItemIdRole:
            ret = self.itemList[index.row()]['id']
        elif role == self.wakItemNameRole:
            ret = self.itemList[index.row()]['name']
        else:
            ret = None
        return ret

    @Slot()
    def reload(self):
        self.beginResetModel()
        self.itemList = settings.OPTIMIZED_ITEM_LIST
        self.endResetModel()

