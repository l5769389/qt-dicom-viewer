pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../theme"

ColumnLayout {
    id: root
    required property string title
    required property real value
    property real from: 1
    property real to: 6
    property real stepSize: 0.5
    property string suffix: " px"
    property string settingName: ""
    signal edited(real value)
    spacing: 8
    RowLayout {
        Layout.fillWidth: true
        Text { Layout.fillWidth: true; text: root.title; color: Theme.textSecondary; font.pixelSize: 12 }
        Text { text: Number(root.value.toFixed(2)) + root.suffix; color: Theme.textPrimary; font.pixelSize: 12 }
    }
    Basic.Slider {
        id: slider
        objectName: "setting-" + root.settingName
        Layout.fillWidth: true
        from: root.from; to: root.to; stepSize: root.stepSize
        value: root.value
        onMoved: root.edited(value)
        implicitHeight: 28
        background: Rectangle {
            x: slider.leftPadding; y: (slider.height - height) / 2
            width: slider.availableWidth; height: 4; radius: 2; color: Theme.borderStrong
            Rectangle { width: parent.width * slider.visualPosition; height: 4; radius: 2; color: Theme.primaryColor }
        }
        handle: Rectangle {
            x: slider.leftPadding + slider.visualPosition * (slider.availableWidth - width)
            y: (slider.height - height) / 2
            implicitWidth: 14; implicitHeight: 14; radius: 7
            color: slider.pressed ? Theme.textPrimary : Theme.primaryColor
            border.color: slider.activeFocus ? Theme.focusBorder : "transparent"
        }
    }
}
