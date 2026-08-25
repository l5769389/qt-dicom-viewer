pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../../components" as Components
import "../../../theme"

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
            iconColor: actionButton.checked
                ? Theme.iconActive
                : actionButton.hovered
                    ? Theme.iconHover
                    : Theme.iconDefault
        }

        Text {
            Layout.fillWidth: true
            text: actionButton.label
            color: actionButton.checked
                ? Theme.textPrimary
                : actionButton.hovered
                    ? Theme.textPrimary
                    : Theme.textSecondary
            font.pixelSize: 12
            verticalAlignment: Text.AlignVCenter
        }
    }

    background: Rectangle {
        color: actionButton.pressed
            ? Theme.controlPressed
            : actionButton.checked
                ? Theme.selectionBackground
                : actionButton.hovered
                    ? Theme.controlHover
                    : Theme.controlBackground
        border.color: actionButton.checked
            ? Theme.selectionBorder
            : actionButton.hovered
                ? Theme.controlHoverBorder
                : Theme.controlBorder
        border.width: 1
        radius: 6
    }
}
