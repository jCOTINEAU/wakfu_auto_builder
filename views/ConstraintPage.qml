import QtQuick 2.12
import QtQuick.Controls

import wakfuConstraintSelector

Item {
    anchors.fill: parent


    WakfuConstraintSelector {
        id: constraintSelectorModel
    }

    Rectangle{
        id: mainRow

        height: childrenRect.height
        width: childrenRect.width
        anchors.horizontalCenter: parent.horizontalCenter


        ConstraintSelector{
            id: pvSelector
            constraintName: 'pvSelector'
            min: 0
            textValue: "PV >= "
            constraintColor: 'red'
        }

        ConstraintSelector{

            anchors {
                top : pvSelector.top
                left : pvSelector.right
                leftMargin: 10
            }

            id: paSelector
            constraintName: 'paSelector'
            min: 0
            textValue: "PA >= "
            constraintColor: 'blue'
        }
        ConstraintSelector{

            anchors {
                top : paSelector.top
                left : paSelector.right
                leftMargin: 10
            }


            id: pmSelector
            constraintName: 'pmSelector'
            min: 0
            textValue: "PM >= "
            constraintColor: 'green'
        }

        ConstraintSelector{

            anchors {
                top : pmSelector.top
                left : pmSelector.right
                leftMargin: 10
            }

            id: pwSelector
            constraintName: 'pwSelector'
            min: 0
            textValue: "PW >= "
            constraintColor: 'steelblue'
        }

        ConstraintSelector{

            anchors {
                top : pwSelector.top
                left : pwSelector.right
                leftMargin: 10
            }

            id: pcSelector
            constraintName: 'pcSelector'
            min: 0
            textValue: "PC >= "
            constraintColor: 'yellow'
        }

    }
    Rectangle{
        id: secondRow

        anchors {
            top : mainRow.bottom
            horizontalCenter: parent.horizontalCenter
        }

        height: childrenRect.height
        width: childrenRect.width

        ConstraintSelector{

            anchors {
                top : parent.top
                left : parent.left
                leftMargin: 10
            }

            id: levelSelector
            constraintName: 'levelSelector'
            min: 0
            textValue: "level <= "
        }

    }
    Rectangle{
        id: thirdRow

        anchors {
            top : secondRow.bottom
            horizontalCenter: parent.horizontalCenter
        }

        height: childrenRect.height
        width: childrenRect.width

        ConstraintSelector{

            anchors {
                top : parent.top
                left : parent.left
                leftMargin: 10
            }

            id: iniSelector
            constraintName: 'iniSelector'
            min: 0
            textValue: "initiative >= "
        }

        ConstraintSelector{

            anchors {
                top : iniSelector.top
                left : iniSelector.right
                leftMargin: 10
            }

            id: ccSelector
            constraintName: 'ccSelector'
            min: 0
            textValue: "chance CC >= "
        }

        ConstraintSelector{

            anchors {
                top : ccSelector.top
                left : ccSelector.right
                leftMargin: 10
            }

            id: dodgeSelector
            constraintName: 'dodgeSelector'
            min: 0
            textValue: "esquive >= "
        }

    }
    Button {
        anchors {
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
        }

        id: solveButton
        text: 'Solve'
        font.pointSize: 25
        onClicked: constraintSelectorModel.solve()
    }
}
