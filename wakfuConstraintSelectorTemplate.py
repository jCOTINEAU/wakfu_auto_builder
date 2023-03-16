# This Python file uses the following encoding: utf-8

from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot,QObject,Signal,Qt,QModelIndex,QByteArray,QAbstractItemModel,QAbstractListModel
from constraint import Constraint
from typing import List

import settings

QML_IMPORT_NAME = "WakfuConstraintSelectorTemplate"
QML_IMPORT_MAJOR_VERSION = 1

@QmlElement
class WakfuConstraintSelectorTemplate(QAbstractListModel):

    wakConstraintColoreRole = Qt.UserRole + 1
    wakConstraintMinRole = Qt.UserRole + 2
    wakConstraintMaxRole = Qt.UserRole + 3
    wakConstraintValueRole = Qt.UserRole + 4
    wakConstraintDefaultValueRole = Qt.UserRole + 5
    wakConstraintTextRole = Qt.UserRole + 6

    def __init__(self,dataArray: [Constraint]=[], parent=None):
        super().__init__(parent=parent)
        self.array: List[Constraint] = dataArray

    def getConstraints(self):
        return self.array

    def rowCount(self, parent=QModelIndex()):
        return len(self.array)

    def roleNames(self):
        default = super().roleNames()
        default[self.wakConstraintColoreRole] = QByteArray(b"customColor")
        default[self.wakConstraintMinRole] = QByteArray(b"customMin")
        default[self.wakConstraintMaxRole] = QByteArray(b"customMax")
        default[self.wakConstraintValueRole] = QByteArray(b"value")
        default[self.wakConstraintDefaultValueRole] = QByteArray(b"defaultValue")
        default[self.wakConstraintTextRole] = QByteArray(b"customText")
        return default

    def data(self, index, role: int):
        if not self.array:
            ret = None
        elif not index.isValid():
            ret = None
        elif role == self.wakConstraintColoreRole:
            ret = self.array[index.row()].getColor()
        elif role == self.wakConstraintMinRole:
            ret = self.array[index.row()].getMin()
        elif role == self.wakConstraintMaxRole:
            ret = self.array[index.row()].getMax()
        elif role == self.wakConstraintValueRole:
            ret = self.array[index.row()].getValue()
        elif role == self.wakConstraintDefaultValueRole:
            ret = self.array[index.row()].getDefault()
        elif role == self.wakConstraintTextRole:
            ret = self.array[index.row()].getText()
        else:
            ret = None
        return ret


    def setData(self,index,value,role: int):
        ret = True
        if not self.array:
            ret = False
        elif not index.isValid():
            ret = False
        elif role == self.wakConstraintColoreRole:
            self.array[index.row()].setColor(value)
        elif role == self.wakConstraintMinRole:
            self.array[index.row()].setMin(value)
        elif role == self.wakConstraintMaxRole:
            self.array[index.row()].setMax(value)
        elif role == self.wakConstraintValueRole:
            self.array[index.row()].setValue(value)
        elif role == self.wakConstraintDefaultValueRole:
            self.array[index.row()].setDefault(value)
        elif role == self.wakConstraintTextRole:
            self.array[index.row()].setText(value)
        else:
            ret = False
        self.dataChanged.emit(0,index,role)
        return ret
