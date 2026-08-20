pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../../components" as Components

Basic.Button {
    id: actionButton

    required property string iconName
    required property string label

    implicitHeight: 40

    contentItem: RowLayout {
        spacing: 10

        Components.AppIcon {
            iconName: actionButton.iconName
            iconSize: 20
            iconColor: actionButton.hovered ? "#d9e6ef" : "#98a6b5"
        }

        Text {
            Layout.fillWidth: true
            text: actionButton.label
            color: actionButton.hovered ? "#ffffff" : "#c2ccd6"
            font.pixelSize: 12
            verticalAlignment: Text.AlignVCenter
        }
    }

    background: Rectangle {
        color: actionButton.pressed
            ? "#29475a"
            : actionButton.hovered ? "#242c35" : "#1d232b"
        border.color: actionButton.hovered ? "#3c596d" : "#2b333d"
        border.width: 1
        radius: 6
    }
}
