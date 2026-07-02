import QtQuick 2.15

// Wakfu item icon with a rarity-colored border.
// Caller sets width/height (the outer square); iconSize is the inner PNG.
// Invisible when gfxId is 0/undefined so cells align naturally when empty.
Rectangle {
    id: root

    property int gfxId: 0
    property int rarity: 0
    property int iconSize: 22

    color: "transparent"
    radius: 5
    visible: gfxId > 0

    border.width: rarity > 1 && rarity <= 7 ? 2 : 0
    border.color: rarity === 2 ? "green"
        : rarity === 3 ? "orange"
        : rarity === 4 ? "yellow"
        : rarity === 5 ? "#6d28d9"
        : rarity === 6 ? "lightblue"
        : rarity === 7 ? "#f9a8d4"
        : "transparent"

    Image {
        id: itemImg
        anchors.centerIn: parent
        width: root.iconSize
        height: root.iconSize
        fillMode: Image.PreserveAspectFit
        sourceSize.width: 64
        sourceSize.height: 64
        asynchronous: true
        cache: true
        source: root.gfxId > 0
            ? "https://static.ankama.com/wakfu/portal/game/item/64/" + root.gfxId + ".png"
            : ""

        // Qt Network on Windows sometimes drops requests when many icons
        // fetch in parallel at startup (per-host connection limit). One
        // silent retry after a short delay covers the flaky cases; the
        // status stays Error if the second attempt also fails.
        property int _retriesLeft: 1
        onStatusChanged: if (status === Image.Error && _retriesLeft > 0) {
            _retriesLeft -= 1
            retryTimer.restart()
        }
        Timer {
            id: retryTimer
            interval: 500
            onTriggered: {
                var s = itemImg.source
                itemImg.source = ""
                itemImg.source = s
            }
        }
    }
}
