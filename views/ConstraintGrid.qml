import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import WakfuConstraintSelectorTemplate
import WakfuStatProfileManager

Item {
    anchors.fill: parent

    WakfuStatProfileManager {
        id: profileSelectorModel
    }

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

            // ── Section: Stat Profile ──
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: profileSection.implicitHeight + 32
                color: mainPage.bgCard
                radius: mainPage.radius
                border.color: mainPage.border
                border.width: 1

                ColumnLayout {
                    id: profileSection
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    Text {
                        text: "Profil de stats"
                        color: mainPage.accent
                        font.pixelSize: 18
                        font.bold: true
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        ComboBox {
                            id: profileCombo
                            Layout.preferredWidth: 300
                            Layout.preferredHeight: 38

                            model: {
                                profileSelectorModel.reload()
                                var items = ["Aucun profil"]
                                for (var i = 0; i < profileSelectorModel.count(); i++) {
                                    items.push(profileSelectorModel.profileNameAt(i))
                                }
                                return items
                            }

                            currentIndex: 0

                            onCurrentIndexChanged: {
                                if (currentIndex <= 0) {
                                    constraintSelectorModel.clearActiveProfile()
                                } else {
                                    var pid = profileSelectorModel.profileIdAt(currentIndex - 1)
                                    constraintSelectorModel.setActiveProfile(pid)
                                }
                            }

                            background: Rectangle {
                                color: mainPage.bgInput
                                radius: 6
                                border.color: profileCombo.activeFocus ? mainPage.accent : mainPage.border
                                border.width: 1
                            }

                            contentItem: Text {
                                text: profileCombo.displayText
                                color: mainPage.textLight
                                font.pixelSize: 14
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 10
                            }

                            delegate: ItemDelegate {
                                width: profileCombo.width
                                contentItem: Text {
                                    text: modelData
                                    color: highlighted ? mainPage.accent : mainPage.textLight
                                    font.pixelSize: 14
                                }
                                highlighted: profileCombo.highlightedIndex === index
                                background: Rectangle {
                                    color: highlighted ? Qt.lighter(mainPage.bgInput, 1.4) : mainPage.bgInput
                                }
                            }

                            popup: Popup {
                                y: profileCombo.height
                                width: profileCombo.width
                                implicitHeight: contentItem.implicitHeight
                                padding: 1
                                contentItem: ListView {
                                    clip: true
                                    implicitHeight: contentHeight
                                    model: profileCombo.popup.visible ? profileCombo.delegateModel : null
                                    ScrollIndicator.vertical: ScrollIndicator {}
                                }
                                background: Rectangle {
                                    color: mainPage.bgInput
                                    border.color: mainPage.border
                                    radius: 6
                                }
                            }
                        }

                        Text {
                            visible: profileCombo.currentIndex > 0
                            text: "Les stats de base seront appliquées aux contraintes"
                            color: mainPage.positive
                            font.pixelSize: 12
                            font.italic: true
                        }

                        Text {
                            visible: profileCombo.currentIndex <= 0
                            text: "Aucun ajustement — contraintes brutes"
                            color: mainPage.textMuted
                            font.pixelSize: 12
                            font.italic: true
                        }
                    }
                }
            }

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

        // Stat Profiles button
        Rectangle {
            width: 200
            height: 50
            radius: mainPage.radius
            color: statProfMouse.containsMouse ? Qt.lighter(mainPage.bgInput, 1.3) : mainPage.bgInput
            border.color: mainPage.accent
            border.width: 1

            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: "Profils de stats"
                color: mainPage.accent
                font.pixelSize: 16
                font.bold: true
            }

            MouseArea {
                id: statProfMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    constraintPage.visible = false
                    statProfilesPage.visible = true
                }
            }
        }

        // Refresh profile ComboBox when constraint page becomes visible
        Connections {
            target: constraintPage
            function onVisibleChanged() {
                if (constraintPage.visible) {
                    var savedIdx = profileCombo.currentIndex
                    var savedId = savedIdx > 0 ? profileSelectorModel.profileIdAt(savedIdx - 1) : ""
                    profileSelectorModel.reload()
                    var items = ["Aucun profil"]
                    for (var i = 0; i < profileSelectorModel.count(); i++) {
                        items.push(profileSelectorModel.profileNameAt(i))
                    }
                    profileCombo.model = items
                    // Restore selection by ID
                    var newIdx = 0
                    if (savedId) {
                        for (var j = 0; j < profileSelectorModel.count(); j++) {
                            if (profileSelectorModel.profileIdAt(j) === savedId) {
                                newIdx = j + 1
                                break
                            }
                        }
                    }
                    profileCombo.currentIndex = newIdx
                }
            }
        }

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
