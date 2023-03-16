import QtQuick 2.12
import QtQuick.Controls 2.12

Rectangle {

    color: 'lightgrey'
    height: localText.height
    width: localText.width + localInput.width
    border.width: 1

    MouseArea {
        id : localMouseArea
        anchors.fill: parent
        hoverEnabled: true

        onEntered: {
            localInput.forceActiveFocus()
        }

        onDoubleClicked: {
            localInput.text=defaultValue
        }
    }

    Text {
        id: localText
        text: qsTr(customText)
        font.pointSize: 25

    }
    TextInput {
        id: localInput
        z: parent.z +1

        font.pointSize: 25
        color: customColor

        anchors.left: localText.right
        anchors.bottom: localText.bottom
        anchors.top: localText.AlignHCenter
        validator: IntValidator{bottom: customMin; top:customMax}

        Component.onCompleted: text=defaultValue!=0 ? defaultValue : ''

        onTextChanged: {
            value = text ==='' ? 0:text
        }
    }

}
