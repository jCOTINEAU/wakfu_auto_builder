# This Python file uses the following encoding: utf-8
from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot,QObject,Signal,Qt,QAbstractListModel,QModelIndex,QByteArray

import settings


QML_IMPORT_NAME = "WakfuItemDetail"
QML_IMPORT_MAJOR_VERSION = 1



@QmlElement
class WakfuItemDetail(QAbstractListModel):

    wakPropertyName = Qt.UserRole + 1
    wakPropertyValue = Qt.UserRole + 2


    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.itemDetails = []

        self.itemDetails.append({'wakPropertyName': 'Name','wakPropertyValue': 'init'})
        self.itemDetails.append({'wakPropertyName': 'Name2','wakPropertyValue': 'init2'})

    def rowCount(self, parent=QModelIndex()):
        return len(self.itemDetails)

    def roleNames(self):
        default = super().roleNames()
        default[self.wakPropertyName] = QByteArray(b"wakPropertyName")
        default[self.wakPropertyValue] = QByteArray(b"wakPropertyValue")
        return default

    def data(self, index, role: int):
        if not self.itemDetails:
            ret = None
        elif not index.isValid():
            ret = None
        elif role == self.wakPropertyName:
            ret = self.itemDetails[index.row()]['wakPropertyName']
        elif role == self.wakPropertyValue:
            ret = self.itemDetails[index.row()]['wakPropertyValue']
        else:
            ret = None
        return ret

    @Slot(int, result=bool)
    def setItemId(self,itemId: int):
        self.beginResetModel()

        item = settings.ITEMS_DATA[itemId]
        self.itemDetails=[]
        self.itemDetails.append({'wakPropertyName': 'Name','wakPropertyValue': item['title']['fr']})

        for equipEffectId,equipEffect in item['definition']['equipEffects'].items():
            description = settings.ACTION_DATA[equipEffectId]['description']['fr']
            self.itemDetails.append({'wakPropertyName': description,'wakPropertyValue': 'dumb'})

        self.endResetModel()
        return True

    @Slot()
    def reset(self):
        self.beginResetModel()
        self.itemDetails=[]
        self.endResetModel()


