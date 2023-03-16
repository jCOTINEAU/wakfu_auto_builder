# This Python file uses the following encoding: utf-8
from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot,QObject,Signal,Qt,QAbstractListModel,QModelIndex,QByteArray

import settings
from settings import simpleActionEnum
from settings import paramsActionEnum
from solver import getEquipEffectValue
from solver import getEquipEffectValueWithParams

QML_IMPORT_NAME = "WakfuItemDetail"
QML_IMPORT_MAJOR_VERSION = 1



@QmlElement
class WakfuItemDetail(QAbstractListModel):

    effect = Qt.UserRole + 1


    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.itemDetails = []


    def rowCount(self, parent=QModelIndex()):
        return len(self.itemDetails)

    def roleNames(self):
        default = super().roleNames()
        default[self.effect] = QByteArray(b"effect")
        return default

    def data(self, index, role: int):
        if not self.itemDetails:
            ret = None
        elif not index.isValid():
            ret = None
        elif role == self.effect:
            ret = self.itemDetails[index.row()]['effect']
        else:
            ret = None
        return ret

    @Slot(int, result=bool)
    def setItemId(self,itemId: int):
        self.beginResetModel()

        item = settings.ITEMS_DATA[itemId]
        self.itemDetails=[]

        for data in simpleActionEnum:
            valueEffect = getEquipEffectValue(item,data.value)
            if valueEffect != 0 :
                description=settings.ACTION_DATA[data.value]['definition']['effect']
                self.itemDetails.append({'effect': description +' : '+ str(valueEffect)})


        for data in paramsActionEnum:
            valueEffect = getEquipEffectValueWithParams(item,data.value)
            if valueEffect != 0 :
                description=settings.ACTION_DATA[data.value]['definition']['effect']
                format='{desc} : {value} on {nb} element'
                descFormated = format.format(desc=description,value=valueEffect,nb=str(item['definition']['equipEffects'][data.value]['effect']['definition']['params'][2]))
                self.itemDetails.append({'effect': descFormated} )

        self.itemDetails = sorted(self.itemDetails,key=lambda x:x['effect'])
        self.endResetModel()
        return True

    @Slot()
    def reset(self):
        self.beginResetModel()
        self.itemDetails=[]
        self.endResetModel()


