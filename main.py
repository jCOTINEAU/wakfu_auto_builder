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


class BrowserLikeNAM(QNetworkAccessManager):
    """QNetworkAccessManager that injects browser-like headers on outgoing
    requests to the Ankama CDN. Their WAF returns 403 for Qt's default
    User-Agent on Windows (observed in app.log).

    NOTE: createRequest may run on a Qt worker thread; avoid Python I/O
    here (print, logging) as it can deadlock or crash the interpreter.
    Logging is done on the `finished` signal instead (main thread).
    """
    _UA = (
        b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        b"AppleWebKit/537.36 (KHTML, like Gecko) "
        b"Chrome/120.0.0.0 Safari/537.36"
    )
    _REFERER = b"https://www.wakfu.com/"
    _TARGET_HOST = "static.ankama.com"

    def __init__(self, parent=None):
        super().__init__(parent)
        # Diagnostic: log status + headers of every finished response so
        # we can distinguish 403 from timeouts, wrong URLs, etc.
        self.finished.connect(self._log_reply)

    def _log_reply(self, reply):
        try:
            url = reply.url().toString()
            if self._TARGET_HOST not in url:
                return
            from PySide6.QtNetwork import QNetworkRequest
            status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            err = reply.error()
            err_str = reply.errorString() if err else "OK"
            def _hdr(name):
                v = reply.rawHeader(name)
                return bytes(v).decode(errors="replace") if v else ""
            server = _hdr("Server")
            cf_ray = _hdr("Cf-Ray")
            content_type = _hdr("Content-Type")
            content_length = _hdr("Content-Length")
            print(f"[http] {url} → status={status} err={err_str}"
                  f" server={server} cf-ray={cf_ray}"
                  f" ct={content_type} cl={content_length}", flush=True)
        except Exception as e:
            print(f"[http-log-err] {e}", flush=True)

    def createRequest(self, op, req, outgoingData=None):
        try:
            if req.url().host() == self._TARGET_HOST:
                if not req.hasRawHeader(b"User-Agent"):
                    req.setRawHeader(b"User-Agent", self._UA)
                if not req.hasRawHeader(b"Referer"):
                    req.setRawHeader(b"Referer", self._REFERER)
        except Exception:
            # Never let a header tweak block the actual network call.
            pass
        if outgoingData is None:
            return super().createRequest(op, req)
        return super().createRequest(op, req, outgoingData)


class DiskCachedNetworkManagerFactory(QQmlNetworkAccessManagerFactory):
    """Attach a persistent disk cache + browser-like headers to every QML
    QNetworkAccessManager.

    Cache dir uses QStandardPaths.CacheLocation which resolves to the
    OS-conventional cache path (Windows: %LOCALAPPDATA%\\<App>\\cache\\,
    macOS: ~/Library/Caches/<App>/, Linux: ~/.cache/<App>/). Writing to
    AppData\\Roaming on Windows silently fails for QNetworkDiskCache.
    """
    def create(self, parent):
        nam = BrowserLikeNAM(parent)
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





