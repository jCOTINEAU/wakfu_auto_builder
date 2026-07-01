# This Python file uses the following encoding: utf-8

from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot, Qt, QAbstractListModel, QModelIndex, QByteArray

import settings
from wakutils import compute_stat_summary

QML_IMPORT_NAME = "WakfuItemStatSum"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class WakfuItemStatSum(QAbstractListModel):

    effect = Qt.UserRole + 1

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.itemStatSumList = []

    def rowCount(self, parent=QModelIndex()):
        return len(self.itemStatSumList)

    def roleNames(self):
        default = super().roleNames()
        default[self.effect] = QByteArray(b"effect")
        return default

    def data(self, index, role: int):
        if not self.itemStatSumList or not index.isValid():
            return None
        if role == self.effect:
            return self.itemStatSumList[index.row()]['effect']
        return None

    @Slot()
    def reload(self):
        self.beginResetModel()
        self.itemStatSumList = compute_stat_summary(settings.OPTIMIZED_ITEM_LIST)
        self.endResetModel()
