import QtQuick 2.15

// Wakfu item icon with a rarity-colored border.
// Caller sets width/height (the outer square); iconSize is the inner PNG.
// If the item icon isn't served by the CDN (some gfxIds legitimately don't
// have an image on Ankama's side), we gracefully fall back to the slot's
// generic SVG (bundled locally, never 404). The rarity border stays either
// way so the user knows the slot + rarity even when the artwork is missing.
Rectangle {
    id: root

    property int gfxId: 0
    property int rarity: 0
    property string slot: ""
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

    // Primary: the item's dedicated icon from the Wakfu CDN.
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
        visible: status === Image.Ready
        source: root.gfxId > 0
            ? "https://static.ankama.com/wakfu/portal/game/item/64/" + root.gfxId + ".png"
            : ""

        // One retry to cover genuine transient failures (network hiccup).
        // Anything more is pointless — Ankama returns a deterministic 403
        // when an item simply doesn't have an icon, no retry will save that.
        property bool _retried: false
        onStatusChanged: if (status === Image.Error && !_retried) {
            _retried = true
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

    // Fallback: the slot's generic SVG, shown when the item icon isn't
    // available (loading, missing, or errored after retry).
    Image {
        anchors.centerIn: parent
        width: root.iconSize
        height: root.iconSize
        fillMode: Image.PreserveAspectFit
        sourceSize.width: 80
        sourceSize.height: 80
        opacity: 0.5
        visible: itemImg.status !== Image.Ready
                 && root.slot !== ""
                 && root.slot !== "OTHER"
        source: visible ? "../assets/slots/" + root.slot + ".svg" : ""
    }
}
