import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import WakfuItemList
import WakfuItemDetail
import WakfuItemStatSum

Item {
    anchors.fill: parent
    id: resultItem

    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        anchors.bottomMargin: backButton.height + 32
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

                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.leftMargin: 12
                            anchors.right: parent.right
                            anchors.rightMargin: 12
                            text: itemName
                            color: mainPage.textLight
                            font.pixelSize: 14
                            elide: Text.ElideRight
                        }

                        MouseArea {
                            id: itemMouse
                            anchors.fill: parent
                            hoverEnabled: true

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

    // ── Back Button ──
    Rectangle {
        id: backButton
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 16
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
}
