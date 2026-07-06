import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import WakfuBuildComparison
import WakfuItemDetail
import WakfuBuildDetails

Item {
    anchors.fill: parent
    id: comparisonPage

    // View mode: "perLine" (default, existing table view) or "cumulated"
    // (two BuildDetailsPanel side by side).
    property string viewMode: "perLine"

    WakfuBuildComparison {
        id: comparisonModel
    }

    // Two build detail models — populated on compare(), used by the
    // cumulated view. Panels sync their toggles via syncPartner.
    WakfuBuildDetails { id: detailsA }
    WakfuBuildDetails { id: detailsB }

    function compare(idA, idB) {
        comparisonModel.compareByIds(idA, idB)
        detailsA.loadBuild(idA)
        detailsB.loadBuild(idB)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        anchors.bottomMargin: compBackBtn.height + 32
        spacing: 16

        // ── Header + mode toggle ──
        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                Text {
                    text: "Comparaison de builds"
                    color: mainPage.accent
                    font.pixelSize: 22
                    font.bold: true
                }

                RowLayout {
                    spacing: 8
                    Text {
                        text: comparisonModel.nameA
                        color: "#6eb5ff"
                        font.pixelSize: 15
                        font.bold: true
                    }
                    Text {
                        text: "vs"
                        color: mainPage.textMuted
                        font.pixelSize: 15
                    }
                    Text {
                        text: comparisonModel.nameB
                        color: "#ffb86e"
                        font.pixelSize: 15
                        font.bold: true
                    }
                }
            }

            // Mode toggle: perLine ↔ cumulated
            Row {
                spacing: 0

                Rectangle {
                    width: 130; height: 34
                    radius: 6
                    color: comparisonPage.viewMode === "perLine" ? mainPage.accent : mainPage.bgInput
                    border.color: mainPage.accent
                    border.width: 1
                    Behavior on color { ColorAnimation { duration: 100 } }
                    Text {
                        anchors.centerIn: parent
                        text: "Ligne par ligne"
                        color: comparisonPage.viewMode === "perLine" ? "#0f0f1a" : mainPage.accent
                        font.pixelSize: 12
                        font.bold: true
                    }
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: comparisonPage.viewMode = "perLine"
                    }
                }
                Rectangle {
                    width: 130; height: 34
                    radius: 6
                    color: comparisonPage.viewMode === "cumulated" ? mainPage.accent : mainPage.bgInput
                    border.color: mainPage.accent
                    border.width: 1
                    Behavior on color { ColorAnimation { duration: 100 } }
                    Text {
                        anchors.centerIn: parent
                        text: "Cumulé"
                        color: comparisonPage.viewMode === "cumulated" ? "#0f0f1a" : mainPage.accent
                        font.pixelSize: 12
                        font.bold: true
                    }
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: comparisonPage.viewMode = "cumulated"
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: mainPage.border
        }

        // ── Stat Delta Table (per-line mode) ──
        Rectangle {
            id: statCard
            visible: comparisonPage.viewMode === "perLine"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredHeight: parent.height * 0.6
            color: mainPage.bgCard
            radius: mainPage.radius
            border.color: mainPage.border
            border.width: 1

            // Shared column proportions (fraction of usable row width)
            property real pStat: 0.34
            property real pValA: 0.22
            property real pDelta: 0.22
            property real pValB: 0.22

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 0

                // Table header – aligned with list rows by reserving scrollbar space
                Item {
                    Layout.fillWidth: true
                    height: 36

                    property real usable: width - 14  // match scrollbar reserve

                    Row {
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.usable
                        spacing: 0

                        Item {
                            width: parent.width * statCard.pStat; height: 36
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left; anchors.leftMargin: 8
                                text: "Statistique"
                                color: mainPage.textMuted; font.pixelSize: 12; font.bold: true
                            }
                        }
                        Item {
                            width: parent.width * statCard.pValA; height: 36
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: comparisonModel.nameA.length > 16
                                      ? comparisonModel.nameA.substring(0, 16) + "…"
                                      : comparisonModel.nameA
                                color: "#6eb5ff"; font.pixelSize: 12; font.bold: true
                            }
                        }
                        Item {
                            width: parent.width * statCard.pDelta; height: 36
                            Text {
                                anchors.centerIn: parent
                                text: "Delta"
                                color: mainPage.textMuted; font.pixelSize: 12; font.bold: true
                            }
                        }
                        Item {
                            width: parent.width * statCard.pValB; height: 36
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: comparisonModel.nameB.length > 16
                                      ? comparisonModel.nameB.substring(0, 16) + "…"
                                      : comparisonModel.nameB
                                color: "#ffb86e"; font.pixelSize: 12; font.bold: true
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: mainPage.border
                }

                // Stat rows
                ListView {
                    id: statListView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: comparisonModel.statModel()
                    clip: true
                    spacing: 0

                    ScrollBar.vertical: ScrollBar {
                        id: statScrollBar
                        policy: ScrollBar.AsNeeded
                        width: 14
                    }

                    delegate: Rectangle {
                        id: statDelegate
                        width: statListView.width - 14   // always reserve scrollbar space
                        height: 34
                        color: index % 2 === 0 ? mainPage.bgInput : "transparent"
                        radius: 2

                        Row {
                            anchors.fill: parent
                            spacing: 0

                            // Stat name
                            Item {
                                width: parent.width * statCard.pStat; height: parent.height
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.left: parent.left; anchors.right: parent.right
                                    anchors.leftMargin: 8; anchors.rightMargin: 4
                                    text: effect
                                    color: mainPage.textLight; font.pixelSize: 13
                                    elide: Text.ElideRight
                                }
                            }

                            // Value A
                            Item {
                                width: parent.width * statCard.pValA; height: parent.height
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    text: valueA
                                    color: "#6eb5ff"; font.pixelSize: 13; font.bold: true
                                }
                            }

                            // Delta (colors inverted for malus stats)
                            Item {
                                width: parent.width * statCard.pDelta; height: parent.height
                                Text {
                                    anchors.centerIn: parent
                                    font.pixelSize: 13; font.bold: true
                                    text: {
                                        if (delta > 0) return "▲ +" + delta
                                        if (delta < 0) return "▼ " + delta
                                        return "="
                                    }
                                    color: {
                                        if (delta === 0) return mainPage.textMuted
                                        var good = isMalus ? (delta < 0) : (delta > 0)
                                        return good ? mainPage.positive : mainPage.negative
                                    }
                                }
                            }

                            // Value B
                            Item {
                                width: parent.width * statCard.pValB; height: parent.height
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    text: valueB
                                    color: "#ffb86e"; font.pixelSize: 13; font.bold: true
                                }
                            }
                        }
                    }
                }
            }
        }

        // ── Item Differences (per-slot table, per-line mode) ──
        Rectangle {
            visible: comparisonPage.viewMode === "perLine"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredHeight: parent.height * 0.3
            color: mainPage.bgCard
            radius: mainPage.radius
            border.color: mainPage.border
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 6

                Text {
                    text: "Équipement par slot"
                    color: mainPage.accent
                    font.pixelSize: 15
                    font.bold: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: mainPage.border
                }

                // Column headers — same geometry as the delegate rows.
                Item {
                    Layout.fillWidth: true
                    height: 20

                    // Same computation as the ListView (kept in sync manually).
                    property real gap: 8
                    property real innerW: width - 14
                    property real slotColW: 150
                    property real statusColW: 32
                    property real cellW: Math.max(80,
                        (innerW - slotColW - statusColW - gap * 4 - 4) / 2)

                    Item {
                        id: hdrSlotCol
                        x: gap + 6 + 4     // align with delegate: 4px stripe reserved
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.slotColW
                        height: parent.height
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: "Slot"
                            color: mainPage.textMuted
                            font.pixelSize: 11
                        }
                    }
                    Text {
                        x: hdrSlotCol.x + hdrSlotCol.width + parent.gap + 38   // + icon column offset
                        anchors.verticalCenter: parent.verticalCenter
                        text: comparisonModel.nameA
                        color: "#6eb5ff"
                        font.pixelSize: 12
                        font.bold: true
                        elide: Text.ElideRight
                    }
                    Text {
                        x: hdrSlotCol.x + hdrSlotCol.width + parent.gap + parent.cellW + parent.gap + 38
                        anchors.verticalCenter: parent.verticalCenter
                        text: comparisonModel.nameB
                        color: "#ffb86e"
                        font.pixelSize: 12
                        font.bold: true
                        elide: Text.ElideRight
                    }
                }

                ListView {
                    id: itemSlotListView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: comparisonModel.itemSlotModel()
                    clip: true
                    spacing: 4

                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }

                    // Shared column geometry — computed once per row.
                    property real rowInner: width - 14   // reserve scrollbar space
                    property real gap: 8
                    property real slotColW: 150
                    property real statusColW: 32
                    property real cellW: Math.max(80,
                        (rowInner - slotColW - statusColW - gap * 4 - 4) / 2)

                    delegate: Rectangle {
                        width: itemSlotListView.rowInner
                        height: 44
                        radius: 5
                        color: {
                            if (status === "onlyA") return Qt.rgba(0.88, 0.33, 0.33, 0.06)
                            if (status === "onlyB") return Qt.rgba(0.30, 0.69, 0.50, 0.06)
                            if (status === "diff")  return Qt.rgba(0.89, 0.72, 0.08, 0.04)
                            return "transparent"
                        }

                        // Left status stripe (thin colored bar) — the primary visual cue.
                        Rectangle {
                            width: 4
                            height: parent.height - 8
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            radius: 2
                            color: status === "onlyA" ? mainPage.negative
                                : status === "onlyB" ? mainPage.positive
                                : status === "diff"  ? mainPage.accent
                                : Qt.rgba(1, 1, 1, 0.08)
                        }

                        // ── Slot column (icon + label) ──
                        Item {
                            id: slotCol
                            anchors.left: parent.left
                            anchors.leftMargin: itemSlotListView.gap + 6
                            anchors.verticalCenter: parent.verticalCenter
                            width: itemSlotListView.slotColW
                            height: parent.height

                            Image {
                                id: slotIcon
                                anchors.left: parent.left
                                anchors.verticalCenter: parent.verticalCenter
                                width: 20; height: 20
                                fillMode: Image.PreserveAspectFit
                                sourceSize.width: 40; sourceSize.height: 40
                                asynchronous: true
                                source: slot && slot !== "OTHER"
                                    ? "../assets/slots/" + slot + ".svg"
                                    : ""
                                opacity: 0.75
                            }
                            Text {
                                anchors.left: slotIcon.right
                                anchors.leftMargin: 8
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                text: slotLabel
                                color: mainPage.textMuted
                                font.pixelSize: 13
                                elide: Text.ElideRight
                            }
                        }

                        // ── Item A cell ──
                        Item {
                            id: cellA
                            anchors.left: slotCol.right
                            anchors.leftMargin: itemSlotListView.gap
                            anchors.verticalCenter: parent.verticalCenter
                            width: itemSlotListView.cellW
                            height: parent.height

                            ItemIcon {
                                id: cellAIcon
                                width: 30; height: 30
                                anchors.left: parent.left
                                anchors.verticalCenter: parent.verticalCenter
                                gfxId: itemAGfxId
                                rarity: itemARarity
                                slot: slot
                                iconSize: 24
                            }
                            Text {
                                anchors.left: parent.left
                                anchors.leftMargin: 38   // 30 icon + 8 gap (always reserved for alignment)
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                text: itemAName !== "" ? itemAName : "—"
                                color: itemAName !== ""
                                    ? (status === "onlyA" || status === "diff" ? "#6eb5ff" : mainPage.textLight)
                                    : mainPage.textMuted
                                font.pixelSize: 13
                                elide: Text.ElideRight
                            }

                            MouseArea {
                                anchors.fill: parent
                                hoverEnabled: true
                                acceptedButtons: Qt.NoButton
                                onEntered: {
                                    if (itemAId > 0) {
                                        cmpDetailPopup.itemDetailModel.setItemId(itemAId)
                                        cmpDetailPopup.visible = true
                                        var g = mapToItem(comparisonPage, 0, 0)
                                        cmpDetailPopup.x = Math.min(g.x + width + 8,
                                            comparisonPage.width - cmpDetailPopup.width - 12)
                                        cmpDetailPopup.y = Math.min(g.y,
                                            comparisonPage.height - cmpDetailPopup.height - 20)
                                    }
                                }
                                onExited: cmpDetailPopup.visible = false
                            }
                        }

                        // ── Item B cell ──
                        Item {
                            id: cellB
                            anchors.left: cellA.right
                            anchors.leftMargin: itemSlotListView.gap
                            anchors.verticalCenter: parent.verticalCenter
                            width: itemSlotListView.cellW
                            height: parent.height

                            ItemIcon {
                                id: cellBIcon
                                width: 30; height: 30
                                anchors.left: parent.left
                                anchors.verticalCenter: parent.verticalCenter
                                gfxId: itemBGfxId
                                rarity: itemBRarity
                                slot: slot
                                iconSize: 24
                            }
                            Text {
                                anchors.left: parent.left
                                anchors.leftMargin: 38
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                text: itemBName !== "" ? itemBName : "—"
                                color: itemBName !== ""
                                    ? (status === "onlyB" || status === "diff" ? "#ffb86e" : mainPage.textLight)
                                    : mainPage.textMuted
                                font.pixelSize: 13
                                elide: Text.ElideRight
                            }

                            MouseArea {
                                anchors.fill: parent
                                hoverEnabled: true
                                acceptedButtons: Qt.NoButton
                                onEntered: {
                                    if (itemBId > 0) {
                                        cmpDetailPopup.itemDetailModel.setItemId(itemBId)
                                        cmpDetailPopup.visible = true
                                        var g = mapToItem(comparisonPage, 0, 0)
                                        cmpDetailPopup.x = Math.min(g.x + width + 8,
                                            comparisonPage.width - cmpDetailPopup.width - 12)
                                        cmpDetailPopup.y = Math.min(g.y,
                                            comparisonPage.height - cmpDetailPopup.height - 20)
                                    }
                                }
                                onExited: cmpDetailPopup.visible = false
                            }
                        }

                        // ── Status badge ──
                        Text {
                            anchors.right: parent.right
                            anchors.rightMargin: itemSlotListView.gap
                            anchors.verticalCenter: parent.verticalCenter
                            width: itemSlotListView.statusColW
                            horizontalAlignment: Text.AlignHCenter
                            text: status === "equal" ? "="
                                : status === "diff"  ? "≠"
                                : status === "onlyA" ? "◀"
                                : status === "onlyB" ? "▶"
                                : ""
                            color: status === "equal" ? mainPage.textMuted
                                : status === "diff"  ? mainPage.accent
                                : status === "onlyA" ? mainPage.negative
                                : status === "onlyB" ? mainPage.positive
                                : "transparent"
                            font.pixelSize: 14
                            font.bold: true
                        }
                    }
                }
            }
        }

        // ── Cumulated view (side-by-side BuildDetailsPanel) ──
        Item {
            visible: comparisonPage.viewMode === "cumulated"
            Layout.fillWidth: true
            Layout.fillHeight: true

            Flickable {
                anchors.fill: parent
                contentHeight: cumulRow.implicitHeight
                clip: true
                flickableDirection: Flickable.VerticalFlick
                boundsBehavior: Flickable.StopAtBounds

                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                RowLayout {
                    id: cumulRow
                    width: parent.width - 12   // scrollbar reserve
                    spacing: 12

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        spacing: 8
                        Text {
                            text: comparisonModel.nameA
                            color: "#6eb5ff"
                            font.pixelSize: 15
                            font.bold: true
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        BuildDetailsPanel {
                            Layout.fillWidth: true
                            model: detailsA
                            syncPartner: detailsB
                        }
                    }

                    Rectangle {
                        width: 1
                        Layout.fillHeight: true
                        color: mainPage.border
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        spacing: 8
                        Text {
                            text: comparisonModel.nameB
                            color: "#ffb86e"
                            font.pixelSize: 15
                            font.bold: true
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        BuildDetailsPanel {
                            Layout.fillWidth: true
                            model: detailsB
                            syncPartner: detailsA
                        }
                    }
                }
            }
        }
    }

    // ── Detail popup (floating card on hover — shared by both cells) ──
    Rectangle {
        id: cmpDetailPopup
        visible: false
        width: 320
        height: Math.max(100, Math.min(cmpDetailList.contentHeight + 72,
                                       comparisonPage.height * 0.6))
        color: mainPage.bgCard
        radius: mainPage.radius
        border.color: mainPage.accent
        border.width: 1
        z: 100

        property alias itemDetailModel: cmpDetailList.model

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8

            Text {
                text: "Détails"
                color: mainPage.accent
                font.pixelSize: 14
                font.bold: true
            }

            ListView {
                id: cmpDetailList
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: WakfuItemDetail {}
                clip: true
                spacing: 2

                delegate: Text {
                    width: cmpDetailList.width
                    text: effect
                    color: mainPage.textLight
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                }
            }
        }
    }

    // ── Back button ──
    Rectangle {
        id: compBackBtn
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 16
        width: 260
        height: 50
        radius: mainPage.radius
        color: compBackMouse.containsMouse ? Qt.lighter(mainPage.bgInput, 1.3) : mainPage.bgInput
        border.color: mainPage.accent
        border.width: 1

        Behavior on color { ColorAnimation { duration: 150 } }

        Text {
            anchors.centerIn: parent
            text: "← Retour aux builds"
            color: mainPage.accent
            font.pixelSize: 16
            font.bold: true
        }

        MouseArea {
            id: compBackMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: {
                comparisonPage.visible = false
                savedBuildsPage.visible = true
            }
        }
    }
}
