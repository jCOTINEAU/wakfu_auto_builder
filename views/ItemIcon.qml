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
    }
}
