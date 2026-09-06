import QtQuick
import QtQuick.Controls.Basic as Basic
import "../theme"

Basic.CheckBox {
    id: control
    implicitHeight: Theme.controlHeight
    spacing: 8
    padding: 4
    hoverEnabled: true
    indicator: Rectangle {
        implicitWidth: 18
        implicitHeight: 18
        x: control.leftPadding
        y: (control.height - height) / 2
        radius: 4
        color: !control.enabled ? Theme.controlDisabled
            : control.checked ? Theme.selectionBackground : Theme.controlBackground
        border.color: !control.enabled ? Theme.controlBorder
            : control.checked ? Theme.selectionBorder : Theme.inputBorder
        AppIcon {
            anchors.centerIn: parent
            iconName: "check"
            iconSize: 14
            visible: control.checked
            iconColor: control.enabled ? Theme.primaryColor : Theme.iconDisabled
        }
    }
    contentItem: Text {
        text: control.text
        color: control.enabled ? Theme.textSecondary : Theme.textDisabled
        font.pixelSize: Theme.bodyFontSize
        verticalAlignment: Text.AlignVCenter
        leftPadding: control.indicator.width + control.spacing
        elide: Text.ElideRight
    }
    background: Rectangle {
        radius: Theme.controlRadius
        color: control.enabled && control.hovered ? Theme.controlHover : "transparent"
        border.width: control.activeFocus ? 2 : 0
        border.color: Theme.focusBorder
    }
}
