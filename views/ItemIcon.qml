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

        // Retry on transient failures. Logs every state transition so we
        // can see what's actually happening (whether Error fires at all,
        // how many retries happen, whether the retry succeeds).
        property int _attempt: 0
        readonly property var _backoffMs: [500, 1500, 3500, 7500]

        onStatusChanged: {
            var name = status === Image.Null ? "Null"
                : status === Image.Ready ? "Ready"
                : status === Image.Loading ? "Loading"
                : status === Image.Error ? "Error"
                : "?"
            console.log("[ItemIcon]", root.gfxId, "status=" + name,
                        "attempt=" + _attempt, "progress=" + progress)
            if (status === Image.Error && _attempt < _backoffMs.length) {
                var base = _backoffMs[_attempt]
                var jittered = base * (0.6 + Math.random() * 0.8)
                console.log("[ItemIcon]", root.gfxId, "retry in", Math.round(jittered), "ms")
                retryTimer.interval = jittered
                _attempt += 1
                retryTimer.restart()
            }
        }

        Timer {
            id: retryTimer
            onTriggered: {
                var s = itemImg.source
                console.log("[ItemIcon]", root.gfxId, "retry firing, reload source")
                itemImg.source = ""
                itemImg.source = s
            }
        }
    }
}
