import os
import settings
from wakutils import setupJson
from paths import resource_path, user_data_dir

# UI zoom. Set QT_SCALE_FACTOR via environment to override at runtime
# (e.g. `QT_SCALE_FACTOR=1.5 python main.py`), otherwise falls back to
# the value below. Applies to fonts, layouts, icons, borders — every-
# thing goes through Qt's scaling pipeline.
os.environ.setdefault("QT_SCALE_FACTOR", "1.3")

import sys
from PySide6.QtCore import QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkDiskCache
from PySide6.QtQml import QQmlApplicationEngine, QQmlNetworkAccessManagerFactory
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


class DiskCachedNetworkManagerFactory(QQmlNetworkAccessManagerFactory):
    """Attach a persistent disk cache to every QML QNetworkAccessManager.

    QML Image URLs (Wakfu CDN item icons) go through this manager. Icons
    are stored on first fetch and served from disk on subsequent launches
    — no more per-host connection-limit flakiness on Windows and offline-
    friendly after the first successful load.
    """
    def create(self, parent):
        nam = QNetworkAccessManager(parent)
        cache = QNetworkDiskCache(nam)
        cache.setCacheDirectory(os.path.join(user_data_dir(), "network-cache"))
        cache.setMaximumCacheSize(50 * 1024 * 1024)   # 50 MB — plenty
        nam.setCache(cache)
        return nam


if __name__ == "__main__":

    #Set up the application window
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    # Hold a strong Python reference to the factory — PySide6 doesn't
    # transfer ownership to the engine, so an anonymous instance gets
    # garbage-collected and QML segfaults on the next fetch.
    _network_factory = DiskCachedNetworkManagerFactory()
    engine.setNetworkAccessManagerFactory(_network_factory)

    settings.initGlobal()
    setupJson()

    engine.rootContext().setContextProperty("dataVersion", settings.DATA_VERSION)
    engine.load(resource_path("views", "mainPage.qml"))
    sys.exit(app.exec())





