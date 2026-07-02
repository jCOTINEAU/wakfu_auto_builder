import os
import sys
import settings
from wakutils import setupJson
from paths import resource_path


def _os_cache_dir():
    """Where to put runtime logs. Pure Python — runs before Qt is loaded,
    so we can't rely on QStandardPaths (which returns "" without an
    initialized QCoreApplication)."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Caches")
    else:
        base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    return os.path.join(base, "WakfuAutoBuilder")


def _redirect_output_to_log_when_frozen():
    """PyInstaller with console=False detaches stdout/stderr; redirect
    them to a log file so we can diagnose runtime issues.

    Log path:
    - Windows: %LOCALAPPDATA%\\WakfuAutoBuilder\\app.log
    - macOS:   ~/Library/Caches/WakfuAutoBuilder/app.log
    - Linux:   ~/.cache/WakfuAutoBuilder/app.log
    """
    if not getattr(sys, "frozen", False):
        return
    try:
        log_dir = _os_cache_dir()
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "app.log")
        f = open(log_path, "w", buffering=1, encoding="utf-8")
        sys.stdout = f
        sys.stderr = f
        print(f"[boot] log file: {log_path}", flush=True)
    except Exception:
        # If logging setup fails, keep the original stdout/stderr rather
        # than losing the app entirely to a bad path/permission issue.
        pass


_redirect_output_to_log_when_frozen()

# UI zoom. Set QT_SCALE_FACTOR via environment to override at runtime
# (e.g. `QT_SCALE_FACTOR=1.5 python main.py`), otherwise falls back to
# the value below. Applies to fonts, layouts, icons, borders — every-
# thing goes through Qt's scaling pipeline.
os.environ.setdefault("QT_SCALE_FACTOR", "1.3")

from PySide6.QtCore import QUrl, QStandardPaths, qInstallMessageHandler
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkDiskCache
from PySide6.QtQml import QQmlApplicationEngine, QQmlNetworkAccessManagerFactory
from PySide6.QtGui import QGuiApplication


def _capture_qt_messages():
    """Route Qt/QML messages (qDebug, console.log, warnings...) to our
    Python stdout so they land in the log file when frozen."""
    def handler(mode, ctx, msg):
        print(f"[qt] {msg}", flush=True)
    qInstallMessageHandler(handler)


_capture_qt_messages()
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
    are stored on first fetch and served from disk on subsequent launches.

    Cache dir uses QStandardPaths.CacheLocation which resolves to the
    OS-conventional cache path (Windows: %LOCALAPPDATA%\\<App>\\cache\\,
    macOS: ~/Library/Caches/<App>/, Linux: ~/.cache/<App>/). Writing to
    AppData\\Roaming on Windows silently fails for QNetworkDiskCache;
    Local is where cache data belongs by OS convention.
    """
    def create(self, parent):
        nam = QNetworkAccessManager(parent)
        cache = QNetworkDiskCache(nam)
        cache_base = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
        cache_dir = os.path.join(cache_base, "network-cache")
        os.makedirs(cache_dir, exist_ok=True)
        cache.setCacheDirectory(cache_dir)
        cache.setMaximumCacheSize(50 * 1024 * 1024)   # 50 MB
        nam.setCache(cache)
        print(f"[network-cache] dir={cache_dir}", flush=True)
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





