pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import "../../../components" as Components
import "../../../theme"

Components.AppButton {
    id: actionButton
    required property string iconName
    required property string label
    property bool placeholder: false
    property string tooltipText: label + (placeholder ? " · 待实现" : "")
    iconSize: 24
    implicitHeight: Theme.toolbarButtonHeight
    minimumButtonWidth: 44
    compact: true
    momentary: true
    enabled: !placeholder
    Accessible.name: label
    Accessible.description: tooltipText
    baseBorderWidth: checked ? 1 : 0
    normalColor: Theme.controlBackground
    contentItem: Item {
        Components.AppIcon {
            anchors.centerIn: parent
            iconName: actionButton.iconName
            iconSize: actionButton.iconSize
            iconColor: !actionButton.enabled ? Theme.iconDisabled : actionButton.checked ? Theme.iconActive : actionButton.hovered ? Theme.iconHover : Theme.iconDefault
        }
    }
    Basic.ToolTip {
        visible: actionButton.hovered || actionButton.visualFocus
        delay: 400
        text: actionButton.tooltipText
        contentItem: Text {
            text: actionButton.tooltipText
            color: Theme.textPrimary
            font.pixelSize: Theme.bodyFontSize
        }
        background: Rectangle {
            color: Theme.elevatedBackground
            border.color: Theme.borderStrong
            radius: Theme.controlRadius
        }
    }
}
