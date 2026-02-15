import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: chip
    width: chipRow.implicitWidth + 24
    height: 36
    radius: 18

    property bool active: value === 1
    property color chipColor: {
        if (customColor === 'black' || customColor === undefined)
            return mainPage.accent
        return customColor
    }

    color: active ? chipColor : mainPage.bgInput
    border.color: active ? chipColor : mainPage.border
    border.width: 1
    opacity: active ? 1.0 : 0.6

    Behavior on color { ColorAnimation { duration: 200 } }
    Behavior on opacity { NumberAnimation { duration: 200 } }

    RowLayout {
        id: chipRow
        anchors.centerIn: parent
        spacing: 6

        Rectangle {
            width: 8
            height: 8
            radius: 4
            color: active ? "#0f0f1a" : mainPage.textMuted
            Behavior on color { ColorAnimation { duration: 200 } }
        }

        Text {
            text: customText
            color: active ? "#0f0f1a" : mainPage.textMuted
            font.pixelSize: 13
            font.bold: active
            Behavior on color { ColorAnimation { duration: 200 } }
        }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor

        onClicked: {
            value = value === 1 ? 0 : 1
        }

        onContainsMouseChanged: {
            if (!active) {
                chip.opacity = containsMouse ? 0.85 : 0.6
            }
        }
    }
}
