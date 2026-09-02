pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "../../../components" as Components
import "../../../theme"

RowLayout {
    id: header

    required property string iconName
    required property string title

    implicitHeight: 32
    spacing: 10

    Rectangle {
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
        radius: 6
        color: Theme.primarySoft

        Components.AppIcon {
            anchors.centerIn: parent
            iconName: header.iconName
            iconSize: 17
            iconColor: Theme.iconActive
        }
    }

    Text {
        Layout.fillWidth: true
        text: header.title
        color: Theme.textPrimary
        font.pixelSize: 14
        font.weight: Font.DemiBold
    }
}
