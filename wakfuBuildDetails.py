# This Python file uses the following encoding: utf-8
"""QML-exposed model for the "Build Details" cumulated stats view.

Wraps stat_totals.compute_totals — loads a saved build + its stat profile,
holds the user's chosen elements and added masteries, and exposes the
computed totals as a JSON string that QML parses reactively.
"""

import json

from PySide6.QtQml import QmlElement
from PySide6.QtCore import QObject, Signal, Slot, Property

import build_manager
import stat_profile_manager
from stat_totals import compute_totals


QML_IMPORT_NAME = "WakfuBuildDetails"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class WakfuBuildDetails(QObject):
    """Backing model for BuildDetails.qml.

    QML pattern: bind to `totalsJson` via `JSON.parse(model.totalsJson)`
    and access the nested structure. Every state change (loadBuild,
    setElementSelected, setMasteryAdded) fires `dataChanged`, so bindings
    re-evaluate.
    """

    dataChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._item_ids = []
        self._profile_stats = {}
        self._build_name = ""
        self._profile_name = ""
        self._chosen_elements = set()
        self._added_masteries = set()

    # ── Loading ─────────────────────────────────────────────────────────

    @Slot(str)
    def loadBuild(self, build_id):
        """Load a saved build by its id (from build_manager)."""
        build = build_manager.get_build(build_id)
        if build is None:
            self._item_ids = []
            self._build_name = ""
            self._profile_stats = {}
            self._profile_name = ""
        else:
            self._item_ids = list(build.get("items", []))
            self._build_name = build.get("name", "")
            profile_id = build.get("profile_id", "")
            profile = stat_profile_manager.get_profile(profile_id) if profile_id else None
            if profile:
                self._profile_stats = profile.get("stats", {})
                self._profile_name = profile.get("name", "")
            else:
                self._profile_stats = {}
                self._profile_name = ""
        self.dataChanged.emit()

    @Slot("QVariantList", str)
    def loadFromItems(self, item_ids, profile_id):
        """Alternate loader — for the BuildComparison side-by-side view
        where we already have item lists in hand and just need the totals."""
        self._item_ids = [int(i) for i in item_ids]
        self._build_name = ""
        profile = stat_profile_manager.get_profile(profile_id) if profile_id else None
        if profile:
            self._profile_stats = profile.get("stats", {})
            self._profile_name = profile.get("name", "")
        else:
            self._profile_stats = {}
            self._profile_name = ""
        self.dataChanged.emit()

    # ── User selections ────────────────────────────────────────────────

    @Slot(str, bool)
    def setElementSelected(self, elem, selected):
        if selected:
            self._chosen_elements.add(elem)
        else:
            self._chosen_elements.discard(elem)
        self.dataChanged.emit()

    @Slot(str, result=bool)
    def isElementSelected(self, elem):
        return elem in self._chosen_elements

    @Slot(str, bool)
    def setMasteryAdded(self, mastery, selected):
        if selected:
            self._added_masteries.add(mastery)
        else:
            self._added_masteries.discard(mastery)
        self.dataChanged.emit()

    @Slot(str, result=bool)
    def isMasteryAdded(self, mastery):
        return mastery in self._added_masteries

    # ── Read-only view of the state ────────────────────────────────────

    @Property(str, notify=dataChanged)
    def buildName(self):
        return self._build_name

    @Property(str, notify=dataChanged)
    def profileName(self):
        return self._profile_name

    @Property(int, notify=dataChanged)
    def itemCount(self):
        return len(self._item_ids)

    @Property(str, notify=dataChanged)
    def totalsJson(self):
        """Serialised compute_totals result. QML parses this with
        JSON.parse and binds sub-fields via property expressions."""
        totals = compute_totals(
            self._item_ids,
            base_profile_stats=self._profile_stats,
            chosen_elements=self._chosen_elements,
            added_masteries=self._added_masteries,
        )
        return json.dumps(totals)
