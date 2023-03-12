import QtQuick 2.12

Rectangle {
    required property string textValue
    required property string constraintName
    required property string constraintColor
    required property string defaultValue
    required property int customMin
    required property int customMax

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
            localInput.text = defaultValue ? defaultValue : ''
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

        text: defaultValue ? defaultValue : ''
        anchors.left: localText.right
        anchors.bottom: localText.bottom
        anchors.top: localText.AlignHCenter
        validator: IntValidator{bottom: customMin; top:customMax ? customMax : 9999}

        onTextChanged: {
            constraintSelectorModel.setConstraintValue(constraintName,text)
        }

    }

}
