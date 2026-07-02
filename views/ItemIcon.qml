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

        // Qt Network on Windows drops some of the 14 concurrent CDN
        // fetches at startup (per-host connection limit). Exponential
        // backoff retries recover the flaky cases; after all retries fail
        // the status stays Error (probably a real 404 for that gfxId).
        property int _attempt: 0
        readonly property var _backoffMs: [500, 1000, 2000]

        onStatusChanged: if (status === Image.Error && _attempt < _backoffMs.length) {
            retryTimer.interval = _backoffMs[_attempt]
            _attempt += 1
            retryTimer.restart()
        }

        Timer {
            id: retryTimer
            onTriggered: {
                var s = itemImg.source
                itemImg.source = ""
                itemImg.source = s
            }
        }
    }
}
