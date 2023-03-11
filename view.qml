// Copyright (C) 2021 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial

import QtQuick 2.12
import QtQuick.Controls 2.12



Page {
    width: 640
    height: 480
    id: mainPage

    Rectangle {
        id: itemDisplay
        width: parent.width/2
        height:parent.height/2
        border.color: "red"
    }

    ListModel {
        id: nameModel
        ListElement { name: "Pa"; value: 6 ; delegateColor: "blue" }
        ListElement { name: "Pm"; value: 5 ; delegateColor: "green" }
    }
    Component {
        id: nameDelegate
        Text {
            text: name+' : '+value;
            font.pixelSize: mainPage.height/25
            color: delegateColor
            height: mainPage.height/10
        }
    }

    ListView {
        width: parent.width/2
        height: parent.height/10
        orientation: ListView.Horizontal

        anchors.right: parent.right
        anchors.top: parent.top
        anchors.left: itemDisplay.right

        spacing: 30
        clip: true
        model: nameModel
        delegate: nameDelegate
    }

}
