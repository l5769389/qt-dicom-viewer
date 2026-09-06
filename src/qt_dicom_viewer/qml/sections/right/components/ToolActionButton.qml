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
    property real iconSize: 20
    property bool placeholder: false

    implicitHeight: 40
    enabled: !placeholder
    Accessible.name: label
    Accessible.description: label + (placeholder ? " · 待实现" : "")

    contentItem: RowLayout {
        spacing: 10

        Components.AppIcon {
            iconName: actionButton.iconName
            iconSize: actionButton.iconSize
            iconColor: !actionButton.enabled ? Theme.iconDisabled : actionButton.checked
                ? Theme.iconActive
                : actionButton.hovered
                    ? Theme.iconHover
                    : Theme.iconDefault
        }

        Text {
            Layout.fillWidth: true
            text: actionButton.label + (actionButton.placeholder ? " · 待" : "")
            color: !actionButton.enabled ? Theme.textDisabled : actionButton.checked
                ? Theme.textPrimary
                : actionButton.hovered
                    ? Theme.textPrimary
                    : Theme.textSecondary
            font.pixelSize: 12
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
        }
    }

    background: Rectangle {
        color: !actionButton.enabled ? Theme.controlDisabled : actionButton.pressed
            ? Theme.controlPressed
            : actionButton.checked
                ? Theme.selectionBackground
                : actionButton.hovered
                    ? Theme.controlHover
                    : Theme.controlBackground
        border.color: actionButton.activeFocus ? Theme.focusBorder : actionButton.checked
            ? Theme.selectionBorder
            : actionButton.hovered
                ? Theme.controlHoverBorder
                : Theme.controlBorder
        border.width: 1
        radius: 6
    }
}
