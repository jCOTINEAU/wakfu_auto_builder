import QtQuick 2.12
import QtQuick.Controls 2.12
import WakfuItemList
import WakfuItemDetail

Item {
    anchors.fill: parent
    id: resultItem

    Rectangle {
        id: leftPane
        width: parent.width/2
        height:parent.height
        border.color: "black"

        ListView {
            model : WakfuItemDetail {}
            id: itemDetail
            z:1
            anchors.left: parent.left
            anchors.right: parent.right
            height: 100*count
            delegate:
                Rectangle {
                color: 'white'
                width: itemDetail.width
                height: childrenRect.height
                Text {
                    text: qsTr(wakPropertyName+" : " +wakPropertyValue)
                }
            }
        }

        ListView {
            visible: true
            id : wakItemList
            anchors.fill: parent
            model: WakfuItemList {}

            delegate: Text {
                text: itemName
                property int itemNameId: itemId
                font.pixelSize: leftPane.height/16
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: {
                        var leftPanePos = mapToItem(leftPane,mouseX,mouseY)
                        itemDetail.y=leftPanePos.y
                        itemDetail.model.setItemId(itemId)
                    }
                }
            }
        }
    }


    ListModel {
        id: nameModel
        ListElement { name: "Pa"; value: 6 ; delegateColor: "blue" }
        ListElement { name: "Pm"; value: 5 ; delegateColor: "green" }
        ListElement { name: "Po"; value: 2 ; delegateColor: "black" }
        ListElement { name: "Pw"; value: 2 ; delegateColor: "lightBlue" }
    }
    Component {
        id: nameDelegate
        Text {
            text: name+' : '+value;
            font.pixelSize: mainPage.height/20
            color: delegateColor
        }
    }

    Rectangle {
        id: rightPane

        width: parent.width/2
        height: parent.height

        anchors.top: parent.top
        anchors.bottom: parent.Bottom
        anchors.right: parent.right
        anchors.left: leftPane.right


        Rectangle {
            id: mainStatRow

            height: parent.height/10
            border.color: 'green'

            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right

            ListView {
                orientation: ListView.Horizontal
                anchors.fill: parent
                spacing: 30
                clip: true
                model: nameModel
                delegate: nameDelegate
            }
        }
        Rectangle {
            id: masteryStatRow
            height: parent.height/6
            border.width: 2

            anchors.top: mainStatRow.bottom
            anchors.left: parent.left
            anchors.right: parent.right

            GridView {
                anchors.fill: parent
                model: nameModel
                delegate: nameDelegate
                cellWidth: parent.width/2
                cellHeight: parent.height/2
            }
        }
    }
}
