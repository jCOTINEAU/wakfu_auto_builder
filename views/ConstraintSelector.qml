import QtQuick 2.12

Rectangle {
    required property string textValue
    required property string constraintName
    required property string constraintColor
    property int min

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
            localInput.text=''
        }
    }

    Text {
        id: localText
        text: qsTr(textValue)
        font.pointSize: 25

    }


    TextInput {
        id: localInput
        z: parent.z +1

        font.pointSize: 25
        color: constraintColor ? constraintColor : 'black'

        anchors.left: localText.right
        anchors.bottom: localText.bottom
        anchors.top: localText.AlignHCenter
        validator: IntValidator{bottom: min ? min : 0}

        onTextChanged: {
            constraintSelectorModel.setConstraintValue(constraintName,text)
        }

    }

}
