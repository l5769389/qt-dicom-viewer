import QtQuick
import QtQuick.Controls.Basic as Basic
import "../theme"

Basic.CheckBox {
    id: control
    implicitHeight: 30
    spacing: 8
    indicator: Rectangle {
        implicitWidth: 17
        implicitHeight: 17
        x: control.leftPadding
        y: (control.height - height) / 2
        radius: 4
        color: control.checked ? Theme.primaryButtonBackground : Theme.controlBackground
        border.color: control.checked ? Theme.selectionBorder : Theme.borderStrong
        Text {
            anchors.centerIn: parent
            text: control.checked ? "✓" : ""
            color: Theme.textPrimary
            font.pixelSize: 13
        }
    }
    contentItem: Text {
        text: control.text
        color: control.enabled ? Theme.textSecondary : Theme.textDisabled
        font.pixelSize: 13
        verticalAlignment: Text.AlignVCenter
        leftPadding: control.indicator.width + control.spacing
    }
}
