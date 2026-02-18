import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import WakfuBuildComparison

Item {
    anchors.fill: parent
    id: comparisonPage

    WakfuBuildComparison {
        id: comparisonModel
    }

    function compare(idA, idB) {
        comparisonModel.compareByIds(idA, idB)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        anchors.bottomMargin: compBackBtn.height + 32
        spacing: 16

        // ── Header ──
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

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: mainPage.border
        }

        // ── Stat Delta Table ──
        Rectangle {
            id: statCard
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

        // ── Item Differences ──
        Rectangle {
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
                spacing: 8

                Text {
                    text: "Différences d'équipement"
                    color: mainPage.accent
                    font.pixelSize: 15
                    font.bold: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: mainPage.border
                }

                ListView {
                    id: itemDiffListView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: comparisonModel.itemDiffModel()
                    clip: true
                    spacing: 2

                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }

                    delegate: Rectangle {
                        width: itemDiffListView.width
                        height: 30
                        radius: 4
                        color: {
                            if (diffType === "added") return Qt.rgba(0.30, 0.69, 0.50, 0.12)
                            if (diffType === "removed") return Qt.rgba(0.88, 0.33, 0.33, 0.12)
                            return "transparent"
                        }

                        Row {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            spacing: 8

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                width: 16
                                text: {
                                    if (diffType === "added") return "+"
                                    if (diffType === "removed") return "−"
                                    return "="
                                }
                                color: {
                                    if (diffType === "added") return mainPage.positive
                                    if (diffType === "removed") return mainPage.negative
                                    return mainPage.textMuted
                                }
                                font.pixelSize: 16
                                font.bold: true
                            }

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                width: parent.width - 16 - 8 - diffLabel.width - 8
                                text: itemName
                                color: {
                                    if (diffType === "added") return mainPage.positive
                                    if (diffType === "removed") return mainPage.negative
                                    return mainPage.textMuted
                                }
                                font.pixelSize: 13
                                elide: Text.ElideRight
                            }

                            Text {
                                id: diffLabel
                                anchors.verticalCenter: parent.verticalCenter
                                text: {
                                    if (diffType === "added") return comparisonModel.nameB + " uniquement"
                                    if (diffType === "removed") return comparisonModel.nameA + " uniquement"
                                    return "commun"
                                }
                                color: mainPage.textMuted
                                font.pixelSize: 11
                                opacity: 0.7
                            }
                        }
                    }
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
