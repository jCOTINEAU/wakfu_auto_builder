import settings
from wakutils import setupJson

import sys
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtGui import QGuiApplication
from wakfuitemlist import WakfuItemList
from wakfuItemDetail import WakfuItemDetail
from wakfuConstraintSelector import WakfuConstraintSelector
from wakfuItemStatSum import WakfuItemStatSum
from wakfuConstraintSelectorTemplate import WakfuConstraintSelectorTemplate
from constraint import Constraint

from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot,QObject


if __name__ == "__main__":

    #Set up the application window
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    settings.initGlobal()
    setupJson()
#    solve()

    engine.load("views/mainPage.qml")
    sys.exit(app.exec())





