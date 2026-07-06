import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import WakfuBuildDetails

// Full-page cumulated-stats view for one saved build.
// Toggle-in via SavedBuilds.qml → "Détails" button.
Item {
    id: detailsPage
    anchors.fill: parent

    // Public: SavedBuilds sets this to route the "back" button to the right place.
    property Item returnPage: null

    WakfuBuildDetails { id: detailsModel }

    function open(buildId, backTo) {
        returnPage = backTo
        detailsModel.loadBuild(buildId)
        visible = true
    }

    // ── Header ──
    RowLayout {
        id: header
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 16
        spacing: 12

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Text {
                text: detailsModel.buildName || "Détails du build"
                color: mainPage.accent
                font.pixelSize: 22
                font.bold: true
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
            Text {
                text: {
                    var bits = [detailsModel.itemCount + " objet(s)"]
                    if (detailsModel.profileName) bits.push("profil : " + detailsModel.profileName)
                    return bits.join("   •   ")
                }
                color: mainPage.textMuted
                font.pixelSize: 12
            }
        }

        Rectangle {
            Layout.preferredWidth: 200
            Layout.preferredHeight: 40
            radius: mainPage.radius
            color: backMouse.containsMouse ? Qt.lighter(mainPage.bgInput, 1.3) : mainPage.bgInput
            border.color: mainPage.accent
            border.width: 1
            Behavior on color { ColorAnimation { duration: 120 } }

            Text {
                anchors.centerIn: parent
                text: "← Retour"
                color: mainPage.accent
                font.pixelSize: 14
                font.bold: true
            }
            MouseArea {
                id: backMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    detailsPage.visible = false
                    if (detailsPage.returnPage) detailsPage.returnPage.visible = true
                }
            }
        }
    }

    // ── Scrollable content ──
    Flickable {
        anchors.top: header.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 16
        anchors.topMargin: 8
        contentHeight: panel.implicitHeight
        clip: true
        flickableDirection: Flickable.VerticalFlick
        boundsBehavior: Flickable.StopAtBounds

        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        BuildDetailsPanel {
            id: panel
            model: detailsModel
            width: parent.width - 12   // reserve scrollbar
        }
    }
}
