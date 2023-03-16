import QtQuick 2.12
import QtQuick.Controls 2.12
import WakfuItemList
import WakfuItemDetail
import WakfuItemStatSum

Item {
    anchors.fill: parent
    id: resultItem

    Button {
        anchors {
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
        }

        z:1
        id: goToConstraintButton
        text: 'go back to constraint'
        font.pointSize: 25
        onClicked: {
            resultPage.visible= false
            constraintPage.visible= true
        }
    }

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
                color: index%2==0 ? 'lightgrey':'lightblue'
                width: itemDetail.width
                height: childrenRect.height
                Text {
                    text: qsTr(effect)
                    font.pointSize: leftPane.height/40
                }
            }
        }

        ListView {
            visible: true
            id : wakItemList
            anchors.fill: parent
            model: WakfuItemList {}
            onVisibleChanged: model.reload()

            delegate: Text {
                text: itemName
                property int itemNameId: itemId
                font.pointSize: leftPane.height/30
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: {
                        var leftPanePos = mapToItem(leftPane,mouseX,mouseY)
                        itemDetail.y=leftPanePos.y
                        itemDetail.model.setItemId(itemId)
                        itemDetail.visible= true
                    }
                    onExited: {
                        itemDetail.visible= false
                    }
                }
            }
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

        ListView {
            id: itemSumDetail
            anchors.fill: parent
            model: WakfuItemStatSum {}
            onVisibleChanged: model.reload()
            delegate: Rectangle {
                color: index%2==0 ? 'lightgrey':'lightblue'
                width: itemDetail.width
                height: childrenRect.height
                Text {
                    text: qsTr(effect)
                    font.pointSize: rightPane.height/40
                }
            }
        }
    }
}
