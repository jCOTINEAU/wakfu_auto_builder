import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import WakfuBuildManager

Item {
    anchors.fill: parent
    id: savedBuildsItem

    WakfuBuildManager {
        id: savedBuildModel
        onLoadSuccess: function(constraintsJson) {
            constraintSelectorModel.importConstraints(constraintsJson)
            savedBuildsPage.visible = false
            resultPage.visible = true
        }
    }

    // ── Selection state for comparison ──
    property var selectedIds: []
    property int selectionCount: selectedIds.length

    function toggleSelection(bid) {
        var idx = selectedIds.indexOf(bid)
        if (idx >= 0) {
            var copy = selectedIds.slice()
            copy.splice(idx, 1)
            selectedIds = copy
        } else {
            if (selectedIds.length >= 2) {
                var copy2 = selectedIds.slice()
                copy2.shift()
                copy2.push(bid)
                selectedIds = copy2
            } else {
                selectedIds = selectedIds.concat([bid])
            }
        }
    }

    function isSelected(bid) {
        return selectedIds.indexOf(bid) >= 0
    }

    function clearSelection() {
        selectedIds = []
    }

    // ── Delete confirmation dialog ──
    property string pendingDeleteId: ""

    Rectangle {
        id: deleteDialog
        visible: false
        anchors.centerIn: parent
        width: 360
        height: 160
        color: mainPage.bgCard
        radius: mainPage.radius
        border.color: mainPage.negative
        border.width: 2
        z: 200

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 24
            spacing: 16

            Text {
                text: "Supprimer ce build ?"
                color: mainPage.textLight
                font.pixelSize: 16
                font.bold: true
            }

            Text {
                text: "Cette action est irréversible."
                color: mainPage.textMuted
                font.pixelSize: 13
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12
                Item { Layout.fillWidth: true }

                Rectangle {
                    width: 90
                    height: 36
                    radius: 6
                    color: delCancelMouse.containsMouse ? Qt.lighter(mainPage.bgInput, 1.3) : mainPage.bgInput
                    border.color: mainPage.border
                    border.width: 1

                    Behavior on color { ColorAnimation { duration: 100 } }

                    Text {
                        anchors.centerIn: parent
                        text: "Annuler"
                        color: mainPage.textMuted
                        font.pixelSize: 13
                    }

                    MouseArea {
                        id: delCancelMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: deleteDialog.visible = false
                    }
                }

                Rectangle {
                    width: 110
                    height: 36
                    radius: 6
                    color: delConfirmMouse.containsMouse ? Qt.lighter(mainPage.negative, 1.2) : mainPage.negative

                    Behavior on color { ColorAnimation { duration: 100 } }

                    Text {
                        anchors.centerIn: parent
                        text: "Supprimer"
                        color: "#ffffff"
                        font.pixelSize: 13
                        font.bold: true
                    }

                    MouseArea {
                        id: delConfirmMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            savedBuildModel.deleteBuild(savedBuildsItem.pendingDeleteId)
                            clearSelection()
                            deleteDialog.visible = false
                        }
                    }
                }
            }
        }
    }

    // ── Dim overlay for delete dialog ──
    Rectangle {
        anchors.fill: parent
        color: "#80000000"
        visible: deleteDialog.visible
        z: 150

        MouseArea {
            anchors.fill: parent
            onClicked: deleteDialog.visible = false
        }
    }

    // ── Main content ──
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        anchors.bottomMargin: bottomBtnRow.height + 32
        spacing: 16

        // Header
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Text {
                text: "Builds sauvegardés"
                color: mainPage.accent
                font.pixelSize: 22
                font.bold: true
                Layout.fillWidth: true
            }

            // Selection hint
            Text {
                visible: selectionCount > 0 && selectionCount < 2
                text: "Sélectionnez 1 build de plus pour comparer"
                color: mainPage.textMuted
                font.pixelSize: 12
                font.italic: true
            }
            Text {
                visible: selectionCount === 2
                text: "2 builds sélectionnés"
                color: mainPage.positive
                font.pixelSize: 12
                font.bold: true
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: mainPage.border
        }

        // Empty state
        Text {
            visible: buildListView.count === 0
            text: "Aucun build sauvegardé.\nLancez une optimisation puis cliquez sur « Sauvegarder »."
            color: mainPage.textMuted
            font.pixelSize: 14
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
            Layout.topMargin: 40
        }

        // Build list
        ListView {
            id: buildListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: savedBuildModel
            clip: true
            spacing: 8
            onVisibleChanged: {
                if (visible) {
                    savedBuildModel.reload()
                    clearSelection()
                }
            }

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
            }

            delegate: Rectangle {
                id: buildRow
                width: buildListView.width
                height: 72
                radius: mainPage.radius

                property bool selected: isSelected(buildId)

                color: {
                    if (selected) return Qt.rgba(0.89, 0.72, 0.08, 0.12)
                    if (buildRowMouse.containsMouse) return Qt.lighter(mainPage.bgCard, 1.3)
                    return mainPage.bgCard
                }
                border.color: {
                    if (selected) return mainPage.accent
                    if (buildRowMouse.containsMouse) return mainPage.accent
                    return mainPage.border
                }
                border.width: selected ? 2 : 1

                Behavior on color { ColorAnimation { duration: 100 } }
                Behavior on border.color { ColorAnimation { duration: 100 } }

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 12

                    // Checkbox for comparison selection
                    Rectangle {
                        width: 28
                        height: 28
                        radius: 6
                        color: buildRow.selected ? mainPage.accent : mainPage.bgInput
                        border.color: buildRow.selected ? mainPage.accent : mainPage.border
                        border.width: 1

                        Behavior on color { ColorAnimation { duration: 100 } }

                        Text {
                            anchors.centerIn: parent
                            text: buildRow.selected ? "✓" : ""
                            color: "#0f0f1a"
                            font.pixelSize: 16
                            font.bold: true
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                toggleSelection(buildId)
                                // Force delegate refresh
                                buildRow.selected = isSelected(buildId)
                            }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Text {
                            text: buildName
                            color: mainPage.textLight
                            font.pixelSize: 16
                            font.bold: true
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }

                        Text {
                            text: buildDate + "  •  " + buildItemCount + " objets"
                            color: mainPage.textMuted
                            font.pixelSize: 12
                        }
                    }

                    // Load button
                    Rectangle {
                        width: 80
                        height: 34
                        radius: 6
                        color: loadBtnMouse.containsMouse ? mainPage.accentDim : mainPage.accent

                        Behavior on color { ColorAnimation { duration: 100 } }

                        Text {
                            anchors.centerIn: parent
                            text: "Charger"
                            color: "#0f0f1a"
                            font.pixelSize: 13
                            font.bold: true
                        }

                        MouseArea {
                            id: loadBtnMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: savedBuildModel.loadBuild(buildId)
                        }
                    }

                    // Delete button
                    Rectangle {
                        width: 34
                        height: 34
                        radius: 6
                        color: delBtnMouse.containsMouse ? Qt.lighter(mainPage.bgInput, 1.5) : mainPage.bgInput
                        border.color: mainPage.negative
                        border.width: 1

                        Behavior on color { ColorAnimation { duration: 100 } }

                        Text {
                            anchors.centerIn: parent
                            text: "✕"
                            color: mainPage.negative
                            font.pixelSize: 16
                        }

                        MouseArea {
                            id: delBtnMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                savedBuildsItem.pendingDeleteId = buildId
                                deleteDialog.visible = true
                            }
                        }
                    }
                }

                MouseArea {
                    id: buildRowMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    propagateComposedEvents: true
                    acceptedButtons: Qt.NoButton
                }
            }
        }
    }

    // ── Bottom Buttons ──
    Row {
        id: bottomBtnRow
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 16
        spacing: 16

        // Back button
        Rectangle {
            id: backBtn
            width: 260
            height: 50
            radius: mainPage.radius
            color: backBtnMouse.containsMouse ? Qt.lighter(mainPage.bgInput, 1.3) : mainPage.bgInput
            border.color: mainPage.accent
            border.width: 1

            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: "← Retour aux contraintes"
                color: mainPage.accent
                font.pixelSize: 16
                font.bold: true
            }

            MouseArea {
                id: backBtnMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    clearSelection()
                    savedBuildsPage.visible = false
                    constraintPage.visible = true
                }
            }
        }

        // Compare button (only when 2 selected)
        Rectangle {
            visible: selectionCount === 2
            width: 200
            height: 50
            radius: mainPage.radius
            color: compareMouse.containsMouse ? Qt.lighter(mainPage.positive, 1.2) : mainPage.positive

            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: "⚖  Comparer"
                color: "#ffffff"
                font.pixelSize: 16
                font.bold: true
            }

            MouseArea {
                id: compareMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    buildComparisonPage.compare(selectedIds[0], selectedIds[1])
                    savedBuildsPage.visible = false
                    buildComparisonPage.visible = true
                }
            }
        }
    }
}
