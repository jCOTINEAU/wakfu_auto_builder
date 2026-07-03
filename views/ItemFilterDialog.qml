import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import WakfuItemSearch

// Modal overlay for adding forced / banned items to the current build.
// Requires constraintSelectorModel to be in scope (defined on mainPage).
Item {
    id: dialogRoot
    anchors.fill: parent
    visible: false
    z: 500

    property int forcedCount: 0
    property int excludedCount: 0
    property var forcedList: []
    property var excludedList: []

    function open() {
        _refresh()
        visible = true
        searchInput.forceActiveFocus()
    }
    function close() { visible = false }

    function _refresh() {
        forcedCount    = constraintSelectorModel.forcedItemCount()
        excludedCount  = constraintSelectorModel.excludedItemCount()
        forcedList     = JSON.parse(constraintSelectorModel.getForcedItemsJson())
        excludedList   = JSON.parse(constraintSelectorModel.getExcludedItemsJson())
    }

    Connections {
        target: constraintSelectorModel
        function onForcedItemsChanged()   { dialogRoot._refresh() }
        function onExcludedItemsChanged() { dialogRoot._refresh() }
    }

    // Dim backdrop — click outside closes.
    Rectangle {
        anchors.fill: parent
        color: "#a0000000"
        MouseArea { anchors.fill: parent; onClicked: dialogRoot.close() }
    }

    // Card
    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(parent.width - 40, 720)
        height: Math.min(parent.height - 40, 640)
        color: mainPage.bgCard
        radius: mainPage.radius
        border.color: mainPage.accent
        border.width: 2

        MouseArea { anchors.fill: parent }   // swallow clicks

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 14

            // ── Header ──
            RowLayout {
                Layout.fillWidth: true
                Text {
                    Layout.fillWidth: true
                    text: "Filtres d'objets"
                    color: mainPage.accent
                    font.pixelSize: 20
                    font.bold: true
                }
                Rectangle {
                    width: 30; height: 30; radius: 4
                    color: closeMouse.containsMouse ? Qt.lighter(mainPage.bgInput, 1.4) : "transparent"
                    Behavior on color { ColorAnimation { duration: 100 } }
                    Text { anchors.centerIn: parent; text: "✕"; color: mainPage.textMuted; font.pixelSize: 16 }
                    MouseArea {
                        id: closeMouse
                        anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                        onClicked: dialogRoot.close()
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: mainPage.border }

            // ── Search bar ──
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Rectangle {
                    Layout.fillWidth: true
                    height: 38
                    color: mainPage.bgInput
                    radius: 6
                    border.color: searchInput.activeFocus ? mainPage.accent : mainPage.border
                    border.width: 1

                    TextInput {
                        id: searchInput
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        color: mainPage.textLight
                        font.pixelSize: 14
                        clip: true
                        selectByMouse: true
                        verticalAlignment: TextInput.AlignVCenter

                        onTextChanged: searchModel.setQuery(text, slotCombo.currentValue || "")

                        Text {
                            anchors.fill: parent
                            verticalAlignment: Text.AlignVCenter
                            text: "Rechercher un objet…"
                            color: mainPage.textMuted
                            font.pixelSize: 14
                            visible: !searchInput.text && !searchInput.activeFocus
                        }
                    }
                }

                ComboBox {
                    id: slotCombo
                    Layout.preferredWidth: 170
                    Layout.preferredHeight: 38
                    textRole: "label"
                    valueRole: "key"
                    // Source of truth is wakutils.SLOT_LABELS_FR — Python side.
                    model: JSON.parse(searchModel.slotOptionsJson())
                    onCurrentValueChanged: searchModel.setQuery(searchInput.text, currentValue || "")
                }
            }

            WakfuItemSearch { id: searchModel }

            // Result count / truncation notice
            Text {
                Layout.fillWidth: true
                text: {
                    if (searchModel.totalMatches === 0) return ""
                    if (searchModel.totalMatches > searchModel.maxResults)
                        return searchModel.maxResults + " sur " + searchModel.totalMatches
                            + " résultats — affinez la recherche pour voir les autres"
                    return searchModel.totalMatches + " résultat" + (searchModel.totalMatches > 1 ? "s" : "")
                }
                color: searchModel.totalMatches > searchModel.maxResults
                    ? mainPage.accent
                    : mainPage.textMuted
                font.pixelSize: 11
                font.italic: true
                visible: text !== ""
            }

            // ── Search results ──
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: mainPage.bgInput
                radius: 6
                border.color: mainPage.border
                border.width: 1

                ListView {
                    id: resultsList
                    anchors.fill: parent
                    anchors.margins: 4
                    model: searchModel
                    clip: true
                    spacing: 2

                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                    delegate: Rectangle {
                        width: resultsList.width - 14
                        height: 42
                        radius: 4
                        color: rowMouse.containsMouse ? Qt.lighter(mainPage.bgInput, 1.3) : "transparent"

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 8
                            anchors.rightMargin: 8
                            spacing: 10

                            ItemIcon {
                                Layout.preferredWidth: 32
                                Layout.preferredHeight: 32
                                gfxId: itemGfxId
                                rarity: itemRarity
                                slot: itemSlot
                                iconSize: 26
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 0
                                Text {
                                    Layout.fillWidth: true
                                    text: itemName
                                    color: mainPage.textLight
                                    font.pixelSize: 13
                                    elide: Text.ElideRight
                                }
                                Text {
                                    text: "lvl " + itemLevel
                                    color: mainPage.textMuted
                                    font.pixelSize: 10
                                }
                            }

                            // Force button
                            Rectangle {
                                property bool isForced: dialogRoot.forcedList.indexOf(itemId) >= 0
                                Layout.preferredWidth: 68
                                Layout.preferredHeight: 26
                                radius: 4
                                color: isForced
                                    ? mainPage.positive
                                    : (forceMouse.containsMouse ? "#6eb5ff" : "transparent")
                                border.color: "#6eb5ff"
                                border.width: 1
                                Behavior on color { ColorAnimation { duration: 100 } }

                                Text {
                                    anchors.centerIn: parent
                                    text: parent.isForced ? "✓ Forcé" : "Forcer"
                                    color: parent.isForced ? "#0f0f1a" : "#6eb5ff"
                                    font.pixelSize: 11
                                    font.bold: true
                                }
                                MouseArea {
                                    id: forceMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (parent.isForced) {
                                            constraintSelectorModel.removeForcedItem(itemId)
                                        } else {
                                            constraintSelectorModel.addForcedItem(itemId)
                                        }
                                    }
                                }
                            }

                            // Ban button
                            Rectangle {
                                property bool isBanned: dialogRoot.excludedList.indexOf(itemId) >= 0
                                Layout.preferredWidth: 68
                                Layout.preferredHeight: 26
                                radius: 4
                                color: isBanned
                                    ? mainPage.negative
                                    : (banMouse.containsMouse ? Qt.lighter(mainPage.negative, 1.2) : "transparent")
                                border.color: mainPage.negative
                                border.width: 1
                                Behavior on color { ColorAnimation { duration: 100 } }

                                Text {
                                    anchors.centerIn: parent
                                    text: parent.isBanned ? "✓ Banni" : "Bannir"
                                    color: parent.isBanned ? "#ffffff" : mainPage.negative
                                    font.pixelSize: 11
                                    font.bold: true
                                }
                                MouseArea {
                                    id: banMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (parent.isBanned) {
                                            constraintSelectorModel.removeExcludedItem(itemId)
                                        } else {
                                            constraintSelectorModel.addExcludedItem(itemId)
                                        }
                                    }
                                }
                            }
                        }

                        MouseArea {
                            id: rowMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            acceptedButtons: Qt.NoButton
                            propagateComposedEvents: true
                        }
                    }

                    // Empty state
                    Text {
                        anchors.centerIn: parent
                        visible: resultsList.count === 0
                        text: searchInput.text || slotCombo.currentValue
                            ? "Aucun objet ne correspond"
                            : "Tapez pour rechercher, ou filtrez par slot"
                        color: mainPage.textMuted
                        font.pixelSize: 13
                        font.italic: true
                    }
                }
            }

            // ── Chip zones ──
            ChipZone {
                Layout.fillWidth: true
                title: "Forcés (" + dialogRoot.forcedCount + ")"
                titleColor: "#6eb5ff"
                borderColor: "#6eb5ff"
                items: dialogRoot.forcedList
                onRemove: (iid) => constraintSelectorModel.removeForcedItem(iid)
            }

            ChipZone {
                Layout.fillWidth: true
                title: "Bannis (" + dialogRoot.excludedCount + ")"
                titleColor: mainPage.negative
                borderColor: mainPage.negative
                items: dialogRoot.excludedList
                onRemove: (iid) => constraintSelectorModel.removeExcludedItem(iid)
            }
        }
    }

    // ── Inline chip-zone component ──
    component ChipZone: Rectangle {
        property string title: ""
        property color titleColor: mainPage.textLight
        property color borderColor: mainPage.border
        property var items: []
        signal remove(int iid)

        visible: items.length > 0
        Layout.preferredHeight: items.length > 0 ? chipCol.implicitHeight + 20 : 0
        color: mainPage.bgInput
        radius: 6
        border.color: borderColor
        border.width: 1

        ColumnLayout {
            id: chipCol
            anchors.fill: parent
            anchors.margins: 10
            spacing: 6

            Text {
                text: title
                color: titleColor
                font.pixelSize: 12
                font.bold: true
            }

            Flow {
                Layout.fillWidth: true
                spacing: 6

                Repeater {
                    model: items
                    delegate: Rectangle {
                        width: chipRow.implicitWidth + 20
                        height: 26
                        radius: 4
                        color: chipMouse.containsMouse ? Qt.lighter(mainPage.bgCard, 1.5) : mainPage.bgCard
                        border.color: borderColor
                        border.width: 1
                        Behavior on color { ColorAnimation { duration: 100 } }

                        Row {
                            id: chipRow
                            anchors.centerIn: parent
                            spacing: 6
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: constraintSelectorModel.getItemName(modelData)
                                color: mainPage.textLight
                                font.pixelSize: 11
                            }
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: "✕"; color: borderColor; font.pixelSize: 11; font.bold: true
                            }
                        }
                        MouseArea {
                            id: chipMouse
                            anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: remove(modelData)
                        }
                    }
                }
            }
        }
    }
}
