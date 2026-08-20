pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "../../../components" as Components

RowLayout {
    id: header

    required property string iconName
    required property string title

    spacing: 8

    Components.AppIcon {
        iconName: header.iconName
        iconSize: 18
        iconColor: "#65b5e8"
    }

    Text {
        Layout.fillWidth: true
        text: header.title
        color: "#dce5ed"
        font.pixelSize: 13
        font.weight: Font.DemiBold
    }
}
