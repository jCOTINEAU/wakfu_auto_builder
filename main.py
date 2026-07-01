import os
import settings
from wakutils import setupJson
from paths import resource_path

# UI zoom. Set QT_SCALE_FACTOR via environment to override at runtime
# (e.g. `QT_SCALE_FACTOR=1.5 python main.py`), otherwise falls back to
# the value below. Applies to fonts, layouts, icons, borders — every-
# thing goes through Qt's scaling pipeline.
os.environ.setdefault("QT_SCALE_FACTOR", "1.3")

import sys
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtGui import QGuiApplication
from wakfuitemlist import WakfuItemList
from wakfuItemDetail import WakfuItemDetail
from wakfuConstraintSelector import WakfuConstraintSelector
from wakfuItemStatSum import WakfuItemStatSum
from wakfuConstraintSelectorTemplate import WakfuConstraintSelectorTemplate
from wakfuBuildManager import WakfuBuildManager
from wakfuBuildComparison import WakfuBuildComparison
from wakfuStatProfileManager import WakfuStatProfileManager
from wakfuItemSearch import WakfuItemSearch
from constraint import Constraint

from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot,QObject


if __name__ == "__main__":

    #Set up the application window
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    settings.initGlobal()
    setupJson()

    engine.rootContext().setContextProperty("dataVersion", settings.DATA_VERSION)
    engine.load(resource_path("views", "mainPage.qml"))
    sys.exit(app.exec())





