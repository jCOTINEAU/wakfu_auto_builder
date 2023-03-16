import QtQuick 2.12
import QtQuick.Controls
import wakfuConstraintSelector
import WakfuConstraintSelectorTemplate


Item {
    anchors.fill: parent

    Button {
        anchors {
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
        }

        id: solveButton
        text: 'Solve'
        font.pointSize: 25
        onClicked: {
            constraintSelectorModel.solve()
            resultPage.visible= true
            constraintPage.visible= false
        }
    }

    WakfuConstraintSelector {
        id: constraintSelectorModel
    }

    Grid {
        id: constraintGrid
        anchors {
            top: parent.top
            left: parent.left
            right: parent.right

        }
        columns: (parent.width/250).toFixed(1)

        Repeater {
            model: constraintSelectorModel.getConstraintModel()
            delegate: ConstraintSelector {}
        }

    }

    Rectangle {
        id: seperatorMaximize
        width: parent.width
        height: childrenRect.height
        border.width: 1

        anchors {
            top:constraintGrid.bottom
        }

        Text {
            text: qsTr("Maximize mastery section")
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }

    Grid {
        id: maximizeMasteryGrid
        anchors {
            top: seperatorMaximize.bottom
            left: seperatorMaximize.left
            right: seperatorMaximize.right
        }

        Repeater {
            model: constraintSelectorModel.getElemMasteryMaximizeModel()
            delegate: MaximizeConstraintSelector {}
        }
    }

    Grid {
        id: maximizeOtherMasteryGrid
        anchors {
            top: maximizeMasteryGrid.bottom
            left: maximizeMasteryGrid.left
            right: maximizeMasteryGrid.right
        }

        Repeater {
            model: constraintSelectorModel.getOtherMasteryMaximizeModel()
            delegate: MaximizeConstraintSelector {}
        }
    }

    Rectangle {
        id: seperatorMaximizeOther
        width: parent.width
        height: childrenRect.height
        border.width: 1

        anchors {
            top:maximizeOtherMasteryGrid.bottom
        }

        Text {
            text: qsTr("Maximize other section")
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }

    Grid {
        id: maximizeOtherRatioGrid
        anchors {
            top: seperatorMaximizeOther.bottom
            left: seperatorMaximizeOther.left
            right: seperatorMaximizeOther.right
        }

        Repeater {
            model: constraintSelectorModel.getOtherMaximizeModel()
            delegate: MaximizeRatioConstraintSelector {}
        }
    }
}
