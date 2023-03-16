# This Python file uses the following encoding: utf-8

from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot,Signal,Qt,QAbstractListModel,QModelIndex,QByteArray

import settings
from settings import simpleActionEnum
from settings import paramsActionEnum
from solver import getEquipEffectValue
from solver import getEquipEffectValueWithParams

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
        if not self.itemStatSumList:
            ret = None
        elif not index.isValid():
            ret = None
        elif role == self.effect:
            ret = self.itemStatSumList[index.row()]['effect']
        else:
            ret = None
        return ret

    @Slot()
    def reload(self):
        self.beginResetModel()
        self.itemStatSumList = []

        for data in simpleActionEnum:
            valueEffect = 0
            for item in settings.OPTIMIZED_ITEM_LIST:
                valueEffect += getEquipEffectValue(settings.ITEMS_DATA[item['id']],data.value)
            if valueEffect != 0 :
                description=settings.ACTION_DATA[data.value]['definition']['effect']
                self.itemStatSumList.append({'effect': description +' : '+ str(valueEffect), 'effectId': data.value, 'value': valueEffect })


        for data in paramsActionEnum:
            valueEffect = 0
            nbItem = 0
            for item in settings.OPTIMIZED_ITEM_LIST:
                tempVal = getEquipEffectValueWithParams(settings.ITEMS_DATA[item['id']],data.value)
                valueEffect += tempVal
                if tempVal != 0:
                    nbItem = settings.ITEMS_DATA[item['id']]['definition']['equipEffects'][data.value]['effect']['definition']['params'][2]
            if valueEffect != 0 :
                description=settings.ACTION_DATA[data.value]['definition']['effect']
                format='{desc} : {value} on {nb} element'
                descFormated = format.format(desc=description,value=valueEffect,nb=str(nbItem))
                self.itemStatSumList.append({'effect': descFormated, 'effectId': data.value, 'value': valueEffect } )
        self.endResetModel()
