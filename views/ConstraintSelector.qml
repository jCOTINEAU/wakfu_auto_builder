import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root

    property bool isToggle: customMin === 0 && customMax === 1
    property bool toggleActive: value === 1
    property color chipColor: {
        if (customColor === 'black' || customColor === undefined)
            return mainPage.accent
        return customColor
    }

    width: isToggle ? toggleRow.implicitWidth + 28 : 220
    height: isToggle ? 36 : 40
    radius: isToggle ? 18 : 6

    color: {
        if (isToggle)
            return toggleActive ? chipColor : mainPage.bgInput
        return localInput.activeFocus ? Qt.lighter(mainPage.bgInput, 1.15) : mainPage.bgInput
    }
    border.color: {
        if (isToggle)
            return toggleActive ? chipColor : mainPage.border
        return localInput.activeFocus ? mainPage.accent : mainPage.border
    }
    border.width: 1
    opacity: isToggle ? (toggleActive ? 1.0 : 0.55) : 1.0

    Behavior on border.color { ColorAnimation { duration: 150 } }
    Behavior on color { ColorAnimation { duration: 150 } }
    Behavior on opacity { NumberAnimation { duration: 150 } }

    // ── Toggle mode (rarity checkboxes) ──
    RowLayout {
        id: toggleRow
        anchors.centerIn: parent
        spacing: 8
        visible: isToggle

        Rectangle {
            width: 18
            height: 18
            radius: 4
            color: toggleActive ? Qt.darker(chipColor, 1.3) : "#1e1e36"
            border.color: toggleActive ? chipColor : mainPage.textMuted
            border.width: 1

            Behavior on color { ColorAnimation { duration: 150 } }
            Behavior on border.color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: "✓"
                color: toggleActive ? chipColor : "transparent"
                font.pixelSize: 13
                font.bold: true
                Behavior on color { ColorAnimation { duration: 150 } }
            }
        }

        Text {
            text: customText.replace(" ==", "")
            color: toggleActive ? (chipColor == mainPage.accent ? mainPage.textLight : chipColor) : mainPage.textMuted
            font.pixelSize: 13
            font.bold: toggleActive
            Behavior on color { ColorAnimation { duration: 150 } }
        }
    }

    MouseArea {
        anchors.fill: parent
        visible: isToggle
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor

        onClicked: {
            value = value === 1 ? 0 : 1
        }

        onContainsMouseChanged: {
            if (isToggle && !toggleActive) {
                root.opacity = containsMouse ? 0.75 : 0.55
            }
        }
    }

    // ── Input mode (stat constraints) ──
    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        spacing: 6
        visible: !isToggle

        Text {
            id: localText
            text: customText
            color: mainPage.textLight
            font.pixelSize: 13
            Layout.fillWidth: true
            elide: Text.ElideRight
        }

        Rectangle {
            Layout.preferredWidth: 60
            Layout.preferredHeight: 26
            radius: 4
            color: "#1e1e36"
            border.color: localInput.activeFocus ? mainPage.accent : "transparent"
            border.width: 1

            TextInput {
                id: localInput
                anchors.fill: parent
                anchors.margins: 4
                horizontalAlignment: TextInput.AlignRight
                verticalAlignment: TextInput.AlignVCenter
                font.pixelSize: 14
                font.bold: true
                color: customColor !== 'black' ? customColor : mainPage.accent
                selectionColor: mainPage.accent
                selectedTextColor: "#0f0f1a"
                clip: true

                validator: IntValidator { bottom: customMin; top: customMax }

                Component.onCompleted: text = value !== 0 ? value : ''

                onTextChanged: {
                    value = text === '' ? 0 : text
                }
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        visible: !isToggle
        hoverEnabled: true
        propagateComposedEvents: true
        cursorShape: Qt.IBeamCursor

        onClicked: function(mouse) {
            localInput.forceActiveFocus()
            mouse.accepted = false
        }

        onDoubleClicked: function(mouse) {
            localInput.text = defaultValue
            mouse.accepted = false
        }
    }
}
