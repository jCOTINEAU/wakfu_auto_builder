import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// Reusable cumulated-stats panel for a single build.
// Caller provides the `model` (WakfuBuildDetails). Reused by BuildDetails.qml
// (single-build page) and by BuildComparison's cumulated mode (side by side).
Item {
    id: panel
    property var model
    // Optional: a second WakfuBuildDetails to keep in sync (element +
    // mastery toggles applied to both). Used by BuildComparison in the
    // cumulated mode so both sides always share the same combo.
    property var syncPartner: null
    // Reactive: re-parses on model.dataChanged (triggered by any state change).
    readonly property var totals: model ? JSON.parse(model.totalsJson) : null

    readonly property var elemInfo: [
        { key: "fire",  label: "Feu",   color: "#e74c3c" },
        { key: "water", label: "Eau",   color: "#3498db" },
        { key: "air",   label: "Air",   color: "#7fb3f0" },
        { key: "earth", label: "Terre", color: "#c58c50" }
    ]
    readonly property var masteryInfo: [
        { key: "crit",     label: "Crit" },
        { key: "melee",    label: "Mêlée" },
        { key: "back",     label: "Dos" },
        { key: "distance", label: "Distance" },
        { key: "berzerk",  label: "Berserk" },
        { key: "heal",     label: "Soin" }
    ]
    readonly property var attrInfo: [
        { key: "PV",           label: "PV" },
        { key: "PA",           label: "PA" },
        { key: "PM",           label: "PM" },
        { key: "PW",           label: "PW" },
        { key: "PO",           label: "PO" },
        { key: "controle",     label: "Contrôle" },
        { key: "initiative",   label: "Init" },
        { key: "coupCritique", label: "CC %" },
        { key: "sagesse",      label: "Sagesse" },
        { key: "PP",           label: "PP" },
        { key: "volonte",      label: "Volonté" },
        { key: "parade",       label: "Parade" },
        { key: "tacle",        label: "Tacle" },
        { key: "esquive",      label: "Esquive" }
    ]

    implicitHeight: mainCol.implicitHeight

    ColumnLayout {
        id: mainCol
        anchors.fill: parent
        spacing: 12

        // ── Element mastery cards (also serve as element selectors) ──
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: panel.elemInfo
                delegate: Rectangle {
                    property bool selected: panel.model && panel.model.isElementSelected(modelData.key)
                    // Recompute selected when data changes.
                    Connections {
                        target: panel.model
                        function onDataChanged() {
                            selected = panel.model.isElementSelected(modelData.key)
                        }
                    }
                    Layout.fillWidth: true
                    Layout.preferredHeight: 92
                    radius: 8
                    color: mainPage.bgCard
                    border.color: selected ? modelData.color : mainPage.border
                    border.width: selected ? 3 : 1
                    opacity: selected ? 1.0 : 0.5
                    Behavior on opacity { NumberAnimation { duration: 150 } }

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 2
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: modelData.label
                            color: modelData.color
                            font.pixelSize: 13
                            font.bold: true
                        }
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: panel.totals ? Math.round(panel.totals.elem_mastery[modelData.key]) : "—"
                            color: mainPage.textLight
                            font.pixelSize: 24
                            font.bold: true
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (!panel.model) return
                            var newVal = !parent.selected
                            panel.model.setElementSelected(modelData.key, newVal)
                            if (panel.syncPartner) panel.syncPartner.setElementSelected(modelData.key, newVal)
                        }
                    }
                }
            }
        }

        // ── Cumulated mastery block ──
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: cumulCol.implicitHeight + 24
            color: mainPage.bgCard
            radius: 8
            border.color: mainPage.accent
            border.width: 1

            ColumnLayout {
                id: cumulCol
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                Text {
                    text: "Maîtrise cumulée effective"
                    color: mainPage.accent
                    font.pixelSize: 14
                    font.bold: true
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Text {
                        Layout.fillWidth: true
                        text: {
                            if (!panel.totals) return "—"
                            var topKey = panel.totals.cumulated_mastery.top_elem
                            var info = panel.elemInfo.find(function(e) { return e.key === topKey }) || { label: topKey }
                            return "Base : " + info.label + " (" + Math.round(panel.totals.cumulated_mastery.top_value) + ")"
                        }
                        color: mainPage.textLight
                        font.pixelSize: 13
                    }
                    Text {
                        text: panel.totals ? Math.round(panel.totals.cumulated_mastery.total) : "—"
                        color: mainPage.accent
                        font.pixelSize: 22
                        font.bold: true
                    }
                }

                Flow {
                    Layout.fillWidth: true
                    spacing: 6

                    Repeater {
                        model: panel.masteryInfo
                        delegate: Rectangle {
                            property bool active: panel.model && panel.model.isMasteryAdded(modelData.key)
                            property int val: panel.totals ? Math.round(panel.totals.non_elem_mastery[modelData.key]) : 0
                            Connections {
                                target: panel.model
                                function onDataChanged() {
                                    active = panel.model.isMasteryAdded(modelData.key)
                                }
                            }
                            width: chipRow.implicitWidth + 20
                            height: 28
                            radius: 14
                            color: active ? mainPage.accent : mainPage.bgInput
                            border.color: active ? mainPage.accent : mainPage.border
                            border.width: 1
                            opacity: active ? 1.0 : 0.65
                            Behavior on opacity { NumberAnimation { duration: 150 } }

                            Row {
                                id: chipRow
                                anchors.centerIn: parent
                                spacing: 5
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: modelData.label
                                    color: active ? "#0f0f1a" : mainPage.textLight
                                    font.pixelSize: 12
                                    font.bold: active
                                }
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: active ? "(+" + val + ")" : val
                                    color: active ? "#0f0f1a" : mainPage.textMuted
                                    font.pixelSize: 11
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (!panel.model) return
                                    var newVal = !parent.active
                                    panel.model.setMasteryAdded(modelData.key, newVal)
                                    if (panel.syncPartner) panel.syncPartner.setMasteryAdded(modelData.key, newVal)
                                }
                            }
                        }
                    }
                }
            }
        }

        // ── Elemental resistances ──
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: resCol.implicitHeight + 24
            color: mainPage.bgCard
            radius: 8
            border.color: mainPage.border
            border.width: 1

            ColumnLayout {
                id: resCol
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                Text {
                    text: "Résistances élémentaires"
                    color: mainPage.accent
                    font.pixelSize: 14
                    font.bold: true
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Repeater {
                        model: panel.elemInfo
                        delegate: ColumnLayout {
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            spacing: 1
                            Text {
                                Layout.alignment: Qt.AlignHCenter
                                text: modelData.label
                                color: modelData.color
                                font.pixelSize: 11
                                font.bold: true
                            }
                            Text {
                                Layout.alignment: Qt.AlignHCenter
                                text: panel.totals
                                    ? Math.round(panel.totals.elem_res_pct[modelData.key]) + " %"
                                    : "—"
                                color: mainPage.textLight
                                font.pixelSize: 17
                                font.bold: true
                            }
                            Text {
                                Layout.alignment: Qt.AlignHCenter
                                text: panel.totals
                                    ? Math.round(panel.totals.elem_res_raw[modelData.key]) + " raw"
                                    : ""
                                color: mainPage.textMuted
                                font.pixelSize: 10
                            }
                        }
                    }
                }
            }
        }

        // ── Attributes + individual masteries ──
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: attrCol.implicitHeight + 24
            color: mainPage.bgCard
            radius: 8
            border.color: mainPage.border
            border.width: 1

            ColumnLayout {
                id: attrCol
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                Text {
                    text: "Statistiques"
                    color: mainPage.accent
                    font.pixelSize: 14
                    font.bold: true
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    rowSpacing: 4
                    columnSpacing: 12

                    Repeater {
                        model: panel.attrInfo
                        delegate: RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            spacing: 6
                            Text {
                                text: modelData.label
                                color: mainPage.textMuted
                                font.pixelSize: 12
                                Layout.preferredWidth: 70
                            }
                            Text {
                                Layout.fillWidth: true
                                horizontalAlignment: Text.AlignRight
                                text: panel.totals ? Math.round(panel.totals.attributes[modelData.key]) : "—"
                                color: mainPage.textLight
                                font.pixelSize: 13
                                font.bold: true
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: mainPage.border
                    Layout.topMargin: 4
                }

                Text {
                    text: "Maîtrises individuelles"
                    color: mainPage.textMuted
                    font.pixelSize: 12
                    font.italic: true
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 3
                    rowSpacing: 4
                    columnSpacing: 12

                    Repeater {
                        model: panel.masteryInfo
                        delegate: RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            spacing: 6
                            Text {
                                text: modelData.label
                                color: mainPage.textMuted
                                font.pixelSize: 12
                            }
                            Text {
                                Layout.fillWidth: true
                                horizontalAlignment: Text.AlignRight
                                text: panel.totals ? Math.round(panel.totals.non_elem_mastery[modelData.key]) : "—"
                                color: mainPage.textLight
                                font.pixelSize: 13
                                font.bold: true
                            }
                        }
                    }
                }
            }
        }
    }
}
