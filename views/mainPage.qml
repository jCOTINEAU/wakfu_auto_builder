// Copyright (C) 2021 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial

import QtQuick 2.12
import QtQuick.Controls 2.12
import WakfuItemList

ApplicationWindow {

    visible: true
    width: 1024
    height: 720

    id: mainPage

    ConstraintGrid {
        visible: true
    }

    Resultitem {
        visible: false
    }

}
