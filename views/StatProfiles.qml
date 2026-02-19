import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import WakfuStatProfileManager

Item {
    anchors.fill: parent
    id: statProfilesPage

    WakfuStatProfileManager {
        id: profileModel
    }

    property bool editorOpen: false
    property string editorMode: "new" // "new" or "edit"
    property string editingProfileName: ""

    // ── Delete confirmation ──
    property string pendingDeleteId: ""

    Rectangle {
        id: profileDeleteDialog
        visible: false
        anchors.centerIn: parent
        width: 360; height: 160
        color: mainPage.bgCard; radius: mainPage.radius
        border.color: mainPage.negative; border.width: 2; z: 200

        ColumnLayout {
            anchors.fill: parent; anchors.margins: 24; spacing: 16

            Text { text: "Supprimer ce profil ?"; color: mainPage.textLight; font.pixelSize: 16; font.bold: true }
            Text { text: "Cette action est irréversible."; color: mainPage.textMuted; font.pixelSize: 13 }

            RowLayout {
                Layout.fillWidth: true; spacing: 12
                Item { Layout.fillWidth: true }

                Rectangle {
                    width: 90; height: 36; radius: 6
                    color: pDelCancelMouse.containsMouse ? Qt.lighter(mainPage.bgInput, 1.3) : mainPage.bgInput
                    border.color: mainPage.border; border.width: 1
                    Behavior on color { ColorAnimation { duration: 100 } }
                    Text { anchors.centerIn: parent; text: "Annuler"; color: mainPage.textMuted; font.pixelSize: 13 }
                    MouseArea { id: pDelCancelMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: profileDeleteDialog.visible = false }
                }

                Rectangle {
                    width: 110; height: 36; radius: 6
                    color: pDelConfirmMouse.containsMouse ? Qt.lighter(mainPage.negative, 1.2) : mainPage.negative
                    Behavior on color { ColorAnimation { duration: 100 } }
                    Text { anchors.centerIn: parent; text: "Supprimer"; color: "#ffffff"; font.pixelSize: 13; font.bold: true }
                    MouseArea {
                        id: pDelConfirmMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                        onClicked: { profileModel.deleteProfile(statProfilesPage.pendingDeleteId); profileDeleteDialog.visible = false }
                    }
                }
            }
        }
    }
    Rectangle { anchors.fill: parent; color: "#80000000"; visible: profileDeleteDialog.visible; z: 150; MouseArea { anchors.fill: parent; onClicked: profileDeleteDialog.visible = false } }

    // ── Save toast ──
    Rectangle {
        id: profileSaveToast; visible: false
        anchors.horizontalCenter: parent.horizontalCenter; anchors.top: parent.top; anchors.topMargin: 20
        width: 280; height: 44; radius: 8; color: mainPage.positive; z: 300
        opacity: visible ? 1.0 : 0.0
        Behavior on opacity { NumberAnimation { duration: 200 } }
        Text { anchors.centerIn: parent; text: "Profil sauvegardé !"; color: "#ffffff"; font.pixelSize: 15; font.bold: true }
        Timer { id: profileToastTimer; interval: 2000; onTriggered: profileSaveToast.visible = false }
    }

    Connections {
        target: profileModel
        function onSaveSuccess() { profileSaveToast.visible = true; profileToastTimer.restart() }
    }

    // ══════════════════════════════════════════
    // LIST VIEW (when editor is closed)
    // ══════════════════════════════════════════
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        anchors.bottomMargin: profileBottomBar.height + 32
        spacing: 16
        visible: !editorOpen

        Text {
            text: "Profils de stats"
            color: mainPage.accent; font.pixelSize: 22; font.bold: true
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: mainPage.border }

        Text {
            visible: profileListView.count === 0
            text: "Aucun profil sauvegardé.\nCréez un profil pour définir les stats de base de votre personnage."
            color: mainPage.textMuted; font.pixelSize: 14
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true; Layout.topMargin: 40
        }

        ListView {
            id: profileListView
            Layout.fillWidth: true; Layout.fillHeight: true
            model: profileModel; clip: true; spacing: 8

            onVisibleChanged: { if (visible) profileModel.reload() }

            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            delegate: Rectangle {
                width: profileListView.width; height: 64; radius: mainPage.radius
                color: profRowMouse.containsMouse ? Qt.lighter(mainPage.bgCard, 1.3) : mainPage.bgCard
                border.color: profRowMouse.containsMouse ? mainPage.accent : mainPage.border
                border.width: 1
                Behavior on color { ColorAnimation { duration: 100 } }

                RowLayout {
                    anchors.fill: parent; anchors.margins: 14; spacing: 12

                    ColumnLayout {
                        Layout.fillWidth: true; spacing: 4
                        Text { text: profileName; color: mainPage.textLight; font.pixelSize: 16; font.bold: true; elide: Text.ElideRight; Layout.fillWidth: true }
                        Text { text: profileDate; color: mainPage.textMuted; font.pixelSize: 12 }
                    }

                    // Edit button
                    Rectangle {
                        width: 80; height: 34; radius: 6
                        color: editBtnMouse.containsMouse ? mainPage.accentDim : mainPage.accent
                        Behavior on color { ColorAnimation { duration: 100 } }
                        Text { anchors.centerIn: parent; text: "Éditer"; color: "#0f0f1a"; font.pixelSize: 13; font.bold: true }
                        MouseArea {
                            id: editBtnMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                profileModel.loadForEditing(profileId)
                                editorMode = "edit"
                                editingProfileName = profileName
                                editorOpen = true
                            }
                        }
                    }

                    // Delete button
                    Rectangle {
                        width: 34; height: 34; radius: 6
                        color: profDelMouse.containsMouse ? Qt.lighter(mainPage.bgInput, 1.5) : mainPage.bgInput
                        border.color: mainPage.negative; border.width: 1
                        Behavior on color { ColorAnimation { duration: 100 } }
                        Text { anchors.centerIn: parent; text: "✕"; color: mainPage.negative; font.pixelSize: 16 }
                        MouseArea {
                            id: profDelMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: { statProfilesPage.pendingDeleteId = profileId; profileDeleteDialog.visible = true }
                        }
                    }
                }

                MouseArea {
                    id: profRowMouse; anchors.fill: parent; hoverEnabled: true
                    propagateComposedEvents: true; acceptedButtons: Qt.NoButton
                }
            }
        }
    }

    // ══════════════════════════════════════════
    // EDITOR VIEW (when editor is open)
    // ══════════════════════════════════════════
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        anchors.bottomMargin: profileBottomBar.height + 32
        spacing: 16
        visible: editorOpen

        Text {
            text: editorMode === "new" ? "Nouveau profil" : "Éditer : " + editingProfileName
            color: mainPage.accent; font.pixelSize: 22; font.bold: true
        }

        // Name input (only for new profiles)
        Rectangle {
            Layout.fillWidth: true; height: 44
            color: mainPage.bgInput; radius: 6
            border.color: profNameInput.activeFocus ? mainPage.accent : mainPage.border; border.width: 1
            visible: editorMode === "new"

            TextInput {
                id: profNameInput
                anchors.fill: parent; anchors.margins: 12
                color: mainPage.textLight; font.pixelSize: 14; clip: true; selectByMouse: true
                Text { anchors.fill: parent; text: "Nom du profil..."; color: mainPage.textMuted; font.pixelSize: 14; visible: !profNameInput.text && !profNameInput.activeFocus }
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: mainPage.border }

        // Stat grid
        Flickable {
            Layout.fillWidth: true; Layout.fillHeight: true
            contentHeight: statGrid.height; clip: true
            flickableDirection: Flickable.VerticalFlick; boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            GridLayout {
                id: statGrid
                width: parent.width - 12
                columns: 3; columnSpacing: 16; rowSpacing: 10

                Repeater {
                    id: statRepeater
                    model: {
                        var keys = JSON.parse(profileModel.statKeysJson())
                        return keys
                    }

                    delegate: RowLayout {
                        Layout.fillWidth: true; spacing: 8

                        property string statKey: modelData

                        Text {
                            text: profileModel.statLabel(statKey)
                            color: mainPage.textLight; font.pixelSize: 13
                            Layout.preferredWidth: 120
                        }

                        Rectangle {
                            Layout.preferredWidth: 80; height: 34
                            color: mainPage.bgInput; radius: 6
                            border.color: statInput.activeFocus ? mainPage.accent : mainPage.border; border.width: 1

                            TextInput {
                                id: statInput
                                anchors.fill: parent; anchors.margins: 8
                                color: mainPage.textLight; font.pixelSize: 14
                                clip: true; selectByMouse: true
                                horizontalAlignment: TextInput.AlignHCenter
                                validator: IntValidator { bottom: -9999; top: 99999 }

                                Component.onCompleted: {
                                    var val = profileModel.getEditingStat(statKey)
                                    text = val !== 0 ? val.toString() : ""
                                }

                                onTextChanged: {
                                    var val = parseInt(text)
                                    if (!isNaN(val)) {
                                        profileModel.setEditingStat(statKey, val)
                                    } else {
                                        profileModel.setEditingStat(statKey, 0)
                                    }
                                }

                                Text {
                                    anchors.centerIn: parent
                                    text: profileModel.statDefault(statKey).toString()
                                    color: mainPage.textMuted; font.pixelSize: 14
                                    visible: !statInput.text && !statInput.activeFocus
                                    opacity: 0.5
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // ── Bottom buttons ──
    Row {
        id: profileBottomBar
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 16
        spacing: 16

        // Back / Cancel
        Rectangle {
            width: 260; height: 50; radius: mainPage.radius
            color: profBackMouse.containsMouse ? Qt.lighter(mainPage.bgInput, 1.3) : mainPage.bgInput
            border.color: mainPage.accent; border.width: 1
            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: editorOpen ? "← Annuler" : "← Retour aux contraintes"
                color: mainPage.accent; font.pixelSize: 16; font.bold: true
            }

            MouseArea {
                id: profBackMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                onClicked: {
                    if (editorOpen) {
                        editorOpen = false
                    } else {
                        statProfilesPage.visible = false
                        constraintPage.visible = true
                    }
                }
            }
        }

        // New profile button (list view only)
        Rectangle {
            visible: !editorOpen
            width: 200; height: 50; radius: mainPage.radius
            color: newProfMouse.containsMouse ? mainPage.accentDim : mainPage.accent
            Behavior on color { ColorAnimation { duration: 150 } }

            Text { anchors.centerIn: parent; text: "+ Nouveau profil"; color: "#0f0f1a"; font.pixelSize: 16; font.bold: true }

            MouseArea {
                id: newProfMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                onClicked: {
                    profileModel.resetEditing()
                    editorMode = "new"
                    editingProfileName = ""
                    profNameInput.text = ""
                    editorOpen = true
                }
            }
        }

        // Save button (editor view only)
        Rectangle {
            visible: editorOpen
            width: 200; height: 50; radius: mainPage.radius
            color: saveProfMouse.containsMouse ? mainPage.accentDim : mainPage.accent
            Behavior on color { ColorAnimation { duration: 150 } }

            Text { anchors.centerIn: parent; text: "Sauvegarder"; color: "#0f0f1a"; font.pixelSize: 16; font.bold: true }

            MouseArea {
                id: saveProfMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                onClicked: {
                    if (editorMode === "new") {
                        profileModel.saveProfile(profNameInput.text)
                    } else {
                        profileModel.overwriteProfile(profileModel.getEditingId())
                    }
                    editorOpen = false
                }
            }
        }
    }
}
