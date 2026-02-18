import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import WakfuItemList
import WakfuBuildManager
import wakfuConstraintSelector

ApplicationWindow {
    visible: true
    width: 1100
    height: 780
    minimumWidth: 800
    minimumHeight: 600
    title: "Wakfu Auto-Builder"
    id: mainPage

    color: "#0f0f1a"

    readonly property color bgDark:    "#0f0f1a"
    readonly property color bgCard:    "#1a1a2e"
    readonly property color bgInput:   "#252540"
    readonly property color accent:    "#e2b714"
    readonly property color accentDim: "#b8960f"
    readonly property color textLight: "#e8e8f0"
    readonly property color textMuted: "#8888a0"
    readonly property color border:    "#2e2e4a"
    readonly property color positive:  "#4caf80"
    readonly property color negative:  "#e05555"
    readonly property int   radius:    8

    font.family: "Segoe UI, Helvetica Neue, Arial, sans-serif"

    // Shared constraint model — accessible from all pages via id
    WakfuConstraintSelector {
        id: constraintSelectorModel
    }

    ConstraintGrid {
        id: constraintPage
        visible: true
    }

    Resultitem {
        id: resultPage
        visible: false
    }

    SavedBuilds {
        id: savedBuildsPage
        visible: false
    }

    BuildComparison {
        id: buildComparisonPage
        visible: false
    }

    // ── Version badge ──
    Text {
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: 10
        text: "Wakfu data v" + dataVersion
        color: mainPage.textMuted
        font.pixelSize: 11
        opacity: 0.7
    }
}
