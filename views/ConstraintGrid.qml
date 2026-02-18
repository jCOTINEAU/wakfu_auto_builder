import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import WakfuConstraintSelectorTemplate

Item {
    anchors.fill: parent

    Flickable {
        id: scrollArea
        anchors.fill: parent
        anchors.margins: 16
        anchors.bottomMargin: solveButton.height + 32
        contentHeight: mainColumn.height
        clip: true
        flickableDirection: Flickable.VerticalFlick
        boundsBehavior: Flickable.StopAtBounds

        ScrollBar.vertical: ScrollBar {
            policy: ScrollBar.AsNeeded
        }

        ColumnLayout {
            id: mainColumn
            width: scrollArea.width - 12
            spacing: 20

            // ── Section: Stat Constraints ──
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: sectionConstraints.implicitHeight + 32
                color: mainPage.bgCard
                radius: mainPage.radius
                border.color: mainPage.border
                border.width: 1

                ColumnLayout {
                    id: sectionConstraints
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    Text {
                        text: "Contraintes"
                        color: mainPage.accent
                        font.pixelSize: 18
                        font.bold: true
                    }

                    Flow {
                        Layout.fillWidth: true
                        spacing: 8

                        Repeater {
                            model: constraintSelectorModel ? constraintSelectorModel.getConstraintModel() : null
                            delegate: ConstraintSelector {}
                        }
                    }
                }
            }

            // ── Section: Elemental Mastery Maximize ──
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: sectionElemMastery.implicitHeight + 32
                color: mainPage.bgCard
                radius: mainPage.radius
                border.color: mainPage.border
                border.width: 1

                ColumnLayout {
                    id: sectionElemMastery
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    Text {
                        text: "Maximiser — Maîtrises élémentaires"
                        color: mainPage.accent
                        font.pixelSize: 18
                        font.bold: true
                    }

                    Flow {
                        Layout.fillWidth: true
                        spacing: 8

                        Repeater {
                            model: constraintSelectorModel ? constraintSelectorModel.getElemMasteryMaximizeModel() : null
                            delegate: MaximizeConstraintSelector {}
                        }
                    }
                }
            }

            // ── Section: Other Mastery Maximize ──
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: sectionOtherMastery.implicitHeight + 32
                color: mainPage.bgCard
                radius: mainPage.radius
                border.color: mainPage.border
                border.width: 1

                ColumnLayout {
                    id: sectionOtherMastery
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    Text {
                        text: "Maximiser — Autres maîtrises"
                        color: mainPage.accent
                        font.pixelSize: 18
                        font.bold: true
                    }

                    Flow {
                        Layout.fillWidth: true
                        spacing: 8

                        Repeater {
                            model: constraintSelectorModel ? constraintSelectorModel.getOtherMasteryMaximizeModel() : null
                            delegate: MaximizeConstraintSelector {}
                        }
                    }
                }
            }

            // ── Section: Other Maximize ──
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: sectionOther.implicitHeight + 32
                color: mainPage.bgCard
                radius: mainPage.radius
                border.color: mainPage.border
                border.width: 1

                ColumnLayout {
                    id: sectionOther
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    Text {
                        text: "Maximiser — Divers"
                        color: mainPage.accent
                        font.pixelSize: 18
                        font.bold: true
                    }

                    Flow {
                        Layout.fillWidth: true
                        spacing: 8

                        Repeater {
                            model: constraintSelectorModel ? constraintSelectorModel.getOtherMaximizeModel() : null
                            delegate: MaximizeRatioConstraintSelector {}
                        }
                    }
                }
            }
        }
    }

    // ── Bottom Button Bar ──
    Row {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 16
        spacing: 16

        // Saved Builds button
        Rectangle {
            width: 200
            height: 50
            radius: mainPage.radius
            color: buildsMouse.containsMouse ? Qt.lighter(mainPage.bgInput, 1.3) : mainPage.bgInput
            border.color: mainPage.accent
            border.width: 1

            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: "📂  Mes builds"
                color: mainPage.accent
                font.pixelSize: 16
                font.bold: true
            }

            MouseArea {
                id: buildsMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    constraintPage.visible = false
                    savedBuildsPage.visible = true
                }
            }
        }

        // Solve button
        Rectangle {
            id: solveButton
            width: 220
            height: 50
            radius: mainPage.radius
            color: solveMouseArea.containsMouse ? mainPage.accentDim : mainPage.accent

            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: "Optimiser"
                color: "#0f0f1a"
                font.pixelSize: 18
                font.bold: true
            }

            MouseArea {
                id: solveMouseArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    constraintSelectorModel.solve()
                    resultPage.visible = true
                    constraintPage.visible = false
                }
            }
        }
    }
}
