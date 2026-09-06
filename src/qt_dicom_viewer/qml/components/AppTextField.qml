import QtQuick
import QtQuick.Controls.Basic as Basic
import "../theme"

Basic.TextField {
    id: control
    implicitHeight: 38
    leftPadding: 12
    rightPadding: 12
    color: enabled ? Theme.textPrimary : Theme.textDisabled
    placeholderTextColor: Theme.textSubtle
    font.pixelSize: 13
    selectByMouse: true
    selectionColor: Theme.selectionBackground
    selectedTextColor: Theme.textPrimary
    background: Rectangle {
        radius: 7
        color: Theme.controlBackground
        border.color: control.activeFocus ? Theme.focusBorder : Theme.borderDefault
    }
}
