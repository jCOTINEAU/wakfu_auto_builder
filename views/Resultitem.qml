import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import WakfuItemList
import WakfuItemDetail
import WakfuItemStatSum
import WakfuBuildManager

Item {
    anchors.fill: parent
    id: resultItem

    WakfuBuildManager {
        id: buildManager
        onSaveSuccess: {
            saveDialog.visible = false
            saveConfirmation.visible = true
            confirmTimer.restart()
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        anchors.bottomMargin: bottomBar.height + 32
        spacing: 16

        // ── Left Pane: Equipment List ──
        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: parent.width / 2
            color: mainPage.bgCard
            radius: mainPage.radius
            border.color: mainPage.border
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                Text {
                    text: "Équipement optimal"
                    color: mainPage.accent
                    font.pixelSize: 18
                    font.bold: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: mainPage.border
                }

                ListView {
                    id: wakItemList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: WakfuItemList {}
                    clip: true
                    spacing: 2
                    onVisibleChanged: model.reload()

                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }

                    delegate: Rectangle {
                        width: wakItemList.width
                        height: 42
                        radius: 6
                        color: itemMouse.containsMouse ? Qt.lighter(mainPage.bgInput, 1.2) : (index % 2 === 0 ? mainPage.bgInput : "transparent")

                        Behavior on color { ColorAnimation { duration: 100 } }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 8
                            spacing: 6

                            Text {
                                Layout.fillWidth: true
                                text: itemName
                                color: mainPage.textLight
                                font.pixelSize: 14
                                elide: Text.ElideRight
                                verticalAlignment: Text.AlignVCenter
                            }

                            Rectangle {
                                width: 60; height: 28; radius: 4
                                color: excludeBtnMouse.containsMouse ? Qt.lighter(mainPage.negative, 1.2) : "transparent"
                                border.color: mainPage.negative; border.width: 1
                                visible: itemMouse.containsMouse
                                Behavior on color { ColorAnimation { duration: 100 } }

                                Text {
                                    anchors.centerIn: parent
                                    text: "Exclure"
                                    color: mainPage.negative
                                    font.pixelSize: 11; font.bold: true
                                }

                                MouseArea {
                                    id: excludeBtnMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        constraintSelectorModel.addExcludedItem(itemId)
                                        detailPopup.visible = false
                                    }
                                }
                            }
                        }

                        MouseArea {
                            id: itemMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            propagateComposedEvents: true
                            acceptedButtons: Qt.NoButton

                            onEntered: {
                                detailPopup.itemDetailModel.setItemId(itemId)
                                detailPopup.visible = true

                                var globalPos = mapToItem(resultItem, 0, 0)
                                detailPopup.x = globalPos.x + width + 8
                                detailPopup.y = Math.min(globalPos.y, resultItem.height - detailPopup.height - 20)
                            }
                            onExited: {
                                detailPopup.visible = false
                            }
                        }
                    }
                }
            }
        }

        // ── Right Pane: Stat Summary ──
        Rectangle {
            Layout.fillHeight: true
            Layout.fillWidth: true
            color: mainPage.bgCard
            radius: mainPage.radius
            border.color: mainPage.border
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                Text {
                    text: "Statistiques totales"
                    color: mainPage.accent
                    font.pixelSize: 18
                    font.bold: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: mainPage.border
                }

                ListView {
                    id: itemSumDetail
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: WakfuItemStatSum {}
                    clip: true
                    spacing: 2
                    onVisibleChanged: model.reload()

                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }

                    delegate: Rectangle {
                        width: itemSumDetail.width
                        height: 36
                        radius: 4
                        color: index % 2 === 0 ? mainPage.bgInput : "transparent"

                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.leftMargin: 12
                            anchors.right: parent.right
                            anchors.rightMargin: 12
                            text: effect
                            color: mainPage.textLight
                            font.pixelSize: 13
                            elide: Text.ElideRight
                        }
                    }
                }
            }
        }
    }

    // ── Detail Popup (floating card on hover) ──
    Rectangle {
        id: detailPopup
        visible: false
        width: 320
        height: Math.max(100, Math.min(detailList.contentHeight + 72, resultItem.height * 0.6))
        color: mainPage.bgCard
        radius: mainPage.radius
        border.color: mainPage.accent
        border.width: 1
        z: 100

        property alias itemDetailModel: detailList.model

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
                id: detailList
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: WakfuItemDetail {}
                clip: true
                spacing: 2

                delegate: Text {
                    width: detailList.width
                    text: effect
                    color: mainPage.textLight
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                }
            }
        }
    }

    // ── Save Dialog (overlay) ──
    Rectangle {
        id: saveDialog
        visible: false
        anchors.centerIn: parent
        width: 420
        height: overwriteSelector.currentIndex === 0 ? 260 : 220
        color: mainPage.bgCard
        radius: mainPage.radius
        border.color: mainPage.accent
        border.width: 2
        z: 200

        Behavior on height { NumberAnimation { duration: 150 } }

        MouseArea {
            anchors.fill: parent
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 24
            spacing: 14

            Text {
                text: "Sauvegarder le build"
                color: mainPage.accent
                font.pixelSize: 18
                font.bold: true
            }

            // Dropdown: new build or overwrite existing
            ComboBox {
                id: overwriteSelector
                Layout.fillWidth: true
                model: {
                    var items = ["Nouveau build"]
                    for (var i = 0; i < buildManager.count(); i++) {
                        items.push("Écraser : " + buildManager.buildNameAt(i))
                    }
                    return items
                }
                currentIndex: 0

                background: Rectangle {
                    color: mainPage.bgInput
                    radius: 6
                    border.color: overwriteSelector.activeFocus ? mainPage.accent : mainPage.border
                    border.width: 1
                }

                contentItem: Text {
                    leftPadding: 10
                    text: overwriteSelector.displayText
                    color: mainPage.textLight
                    font.pixelSize: 14
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }

                popup: Popup {
                    y: overwriteSelector.height
                    width: overwriteSelector.width
                    implicitHeight: Math.min(contentItem.implicitHeight + 2, 200)
                    padding: 1

                    background: Rectangle {
                        color: mainPage.bgCard
                        radius: 6
                        border.color: mainPage.border
                        border.width: 1
                    }

                    contentItem: ListView {
                        clip: true
                        implicitHeight: contentHeight
                        model: overwriteSelector.popup.visible ? overwriteSelector.delegateModel : null
                        currentIndex: overwriteSelector.highlightedIndex
                        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                    }
                }

                delegate: ItemDelegate {
                    width: overwriteSelector.width
                    height: 36

                    background: Rectangle {
                        color: highlighted ? Qt.lighter(mainPage.bgInput, 1.4) : mainPage.bgInput
                    }

                    contentItem: Text {
                        text: modelData
                        color: index === 0 ? mainPage.accent : mainPage.textLight
                        font.pixelSize: 13
                        font.bold: index === 0
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 8
                        elide: Text.ElideRight
                    }

                    highlighted: overwriteSelector.highlightedIndex === index
                }
            }

            // Name input — only visible for new builds
            Rectangle {
                Layout.fillWidth: true
                height: 40
                color: mainPage.bgInput
                radius: 6
                border.color: saveNameInput.activeFocus ? mainPage.accent : mainPage.border
                border.width: 1
                visible: overwriteSelector.currentIndex === 0

                TextInput {
                    id: saveNameInput
                    anchors.fill: parent
                    anchors.margins: 10
                    color: mainPage.textLight
                    font.pixelSize: 14
                    clip: true
                    selectByMouse: true

                    Text {
                        anchors.fill: parent
                        text: "Nom du build..."
                        color: mainPage.textMuted
                        font.pixelSize: 14
                        visible: !saveNameInput.text && !saveNameInput.activeFocus
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Item { Layout.fillWidth: true }

                Rectangle {
                    width: 100
                    height: 38
                    radius: 6
                    color: cancelMouse.containsMouse ? Qt.lighter(mainPage.bgInput, 1.3) : mainPage.bgInput
                    border.color: mainPage.border
                    border.width: 1

                    Behavior on color { ColorAnimation { duration: 100 } }

                    Text {
                        anchors.centerIn: parent
                        text: "Annuler"
                        color: mainPage.textMuted
                        font.pixelSize: 14
                    }

                    MouseArea {
                        id: cancelMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            saveDialog.visible = false
                            saveNameInput.text = ""
                            overwriteSelector.currentIndex = 0
                        }
                    }
                }

                Rectangle {
                    width: 120
                    height: 38
                    radius: 6
                    color: confirmMouse.containsMouse ? mainPage.accentDim : mainPage.accent

                    Behavior on color { ColorAnimation { duration: 100 } }

                    Text {
                        anchors.centerIn: parent
                        text: overwriteSelector.currentIndex === 0 ? "Sauvegarder" : "Écraser"
                        color: "#0f0f1a"
                        font.pixelSize: 14
                        font.bold: true
                    }

                    MouseArea {
                        id: confirmMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            var cJson = constraintSelectorModel.exportConstraints()
                            if (overwriteSelector.currentIndex === 0) {
                                buildManager.saveCurrent(saveNameInput.text, cJson)
                            } else {
                                var buildIdx = overwriteSelector.currentIndex - 1
                                var bid = buildManager.buildIdAt(buildIdx)
                                buildManager.overwriteCurrent(bid, cJson)
                            }
                            saveNameInput.text = ""
                            overwriteSelector.currentIndex = 0
                        }
                    }
                }
            }
        }
    }

    // ── Save confirmation toast ──
    Rectangle {
        id: saveConfirmation
        visible: false
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 20
        width: 280
        height: 44
        radius: 8
        color: mainPage.positive
        z: 300
        opacity: visible ? 1.0 : 0.0

        Behavior on opacity { NumberAnimation { duration: 200 } }

        Text {
            anchors.centerIn: parent
            text: "Build sauvegardé !"
            color: "#ffffff"
            font.pixelSize: 15
            font.bold: true
        }

        Timer {
            id: confirmTimer
            interval: 2000
            onTriggered: saveConfirmation.visible = false
        }
    }

    // ── Dim overlay behind save dialog ──
    Rectangle {
        anchors.fill: parent
        color: "#80000000"
        visible: saveDialog.visible
        z: 150

        MouseArea {
            anchors.fill: parent
            onClicked: {
                saveDialog.visible = false
                saveNameInput.text = ""
            }
        }
    }

    // ── Bottom Button Bar ──
    Row {
        id: bottomBar
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 16
        spacing: 16

        // Back button
        Rectangle {
            id: backButton
            width: 260
            height: 50
            radius: mainPage.radius
            color: backMouse.containsMouse ? Qt.lighter(mainPage.bgInput, 1.3) : mainPage.bgInput
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
                id: backMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    resultPage.visible = false
                    constraintPage.visible = true
                }
            }
        }

        // Save button
        Rectangle {
            id: saveButton
            width: 200
            height: 50
            radius: mainPage.radius
            color: saveMouse.containsMouse ? mainPage.accentDim : mainPage.accent

            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: "💾  Sauvegarder"
                color: "#0f0f1a"
                font.pixelSize: 16
                font.bold: true
            }

            MouseArea {
                id: saveMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    buildManager.reload()
                    overwriteSelector.currentIndex = 0
                    overwriteSelector.model = (function() {
                        var items = ["Nouveau build"]
                        for (var i = 0; i < buildManager.count(); i++) {
                            items.push("Écraser : " + buildManager.buildNameAt(i))
                        }
                        return items
                    })()
                    saveDialog.visible = true
                    saveNameInput.forceActiveFocus()
                }
            }
        }
    }
}
