import settings
from wakutils import setupJson
from solver import solve

import sys
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtGui import QGuiApplication
from wakfuitemlist import WakfuItemList
from wakfuItemDetail import WakfuItemDetail
from wakfuConstraintSelector import WakfuConstraintSelector


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




