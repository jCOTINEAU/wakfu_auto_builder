import QtQuick 2.12
import QtQuick.Controls
import wakfuConstraintSelector


Item {
    anchors.fill: parent

    Button {
        z : 1
        anchors {
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
        }

        id: solveButton
        text: 'Solve'
        font.pointSize: 25
        onClicked: constraintSelectorModel.solve()
    }

    Grid {
        WakfuConstraintSelector {
            id: constraintSelectorModel
        }

        id: constraintGrid
        anchors.fill: parent

        Repeater {
            model: constraintModel
            delegate: ConstraintSelector {}
        }

        ListModel {
            id: constraintModel

            ListElement {
                constraintName: 'levelSelector'
                textValue: "level <= "
            }
            ListElement {
                constraintColor: 'red'
                constraintName: 'pvSelector'
                textValue: "PV >= "
            }
            ListElement {
                constraintColor: 'blue'
                constraintName: 'paSelector'
                textValue: "PA >= "
            }
            ListElement {
                constraintColor: 'green'
                constraintName: 'pmSelector'
                textValue: "PM >= "
            }
            ListElement {
                constraintColor: 'steelblue'
                constraintName: 'pwSelector'
                textValue: "PW >= "
            }
            ListElement {
                constraintColor: 'yellow'
                constraintName: 'pcSelector'
                textValue: "PC >= "
            }
            ListElement {
                constraintName: 'iniSelector'
                textValue: "initiative >= "
            }
            ListElement {
                constraintName: 'ccSelector'
                textValue: "chance CC >= "
            }
            ListElement {
                constraintName: 'dodgeSelector'
                textValue: "esquive >= "
            }
            ListElement {
                constraintName: 'wisdomSelector'
                textValue: "sagesse >= "
            }
            ListElement {
                constraintName: 'ppSelector'
                textValue: "prospection >= "
            }
            ListElement {
                constraintName: 'willSelector'
                textValue: "volonté >= "
            }
            ListElement {
                constraintName: 'blockSelector'
                textValue: "parade >= "
            }
            ListElement {
                constraintName: 'lockSelector'
                textValue: "tacle >= "
            }
            ListElement {
                constraintName: 'dodgeSelector'
                textValue: "esquive >= "
            }
        }

    }
}
