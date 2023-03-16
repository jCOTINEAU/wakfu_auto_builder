import QtQuick 2.12
import QtQuick.Controls 2.12

Rectangle {

    color: value == 1 ? customColor != 'black' ? customColor : 'yellow' : 'lightgrey'
    height: localText.height
    width: localText.width
    border.width: value == 1 ? 2 : 1

    MouseArea {
        anchors.fill: parent
        onClicked: value = value == 1 ? 0 : 1
    }

    Text {
        id: localText
        text: qsTr(customText)
        font.pointSize: 25

    }
}
