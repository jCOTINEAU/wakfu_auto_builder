import QtQuick 2.12
import QtQuick.Controls
import wakfuConstraintSelector


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
        onClicked: constraintSelectorModel.solve()
    }

    Grid {
        WakfuConstraintSelector {
            id: constraintSelectorModel
        }

        id: constraintGrid
        anchors.fill: parent
        columns: (parent.width/250).toFixed(1)

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
            ListElement {
                constraintName: 'rarityCommonSelector'
                defaultValue: '1'
                textValue: "commun == "
                customMax: 1
                customMin: 0
                constraintColor: 'white'
            }
            ListElement {
                constraintName: 'rarityRareSelector'
                defaultValue: '1'
                textValue: "rare == "
                customMax: 1
                customMin: 0
                constraintColor: 'green'
            }
            ListElement {
                constraintName: 'rarityMythicalSelector'
                defaultValue: '1'
                textValue: "mythique == "
                customMax: 1
                customMin: 0
                constraintColor: 'orange'
            }
            ListElement {
                constraintName: 'rarityLengendarySelector'
                defaultValue: '1'
                textValue: "legendaire == "
                customMax: 1
                customMin: 0
                constraintColor: 'khaki'
            }
            ListElement {
                constraintName: 'rarityMemorySelector'
                defaultValue: '1'
                textValue: "souvenir == "
                constraintColor: 'lightblue'
                customMax: 1
                customMin: 0
            }
            ListElement {
                constraintName: 'rarityEpicSelector'
                defaultValue: '1'
                textValue: "epique == "
                customMax: 1
                customMin: 0
                constraintColor: 'purple'
            }
            ListElement {
                constraintName: 'rarityRelicSelector'
                defaultValue: '1'
                textValue: "relique == "
                customMax: 1
                customMin: 0
                constraintColor: 'fuchsia'
            }
        }

    }
}
