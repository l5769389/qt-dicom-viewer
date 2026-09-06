pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"

RowLayout {
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
    Text {
        Layout.preferredWidth: 76
        text: root.title
        color: Theme.textSecondary
        font.pixelSize: 12
        wrapMode: Text.Wrap
    }
    Components.AppSlider {
        objectName: "setting-" + root.settingName
        Layout.fillWidth: true
        from: root.from; to: root.to; stepSize: root.stepSize
        value: root.value
        Accessible.name: root.title
        onMoved: root.edited(value)
    }
    Text {
        Layout.preferredWidth: 44
        horizontalAlignment: Text.AlignRight
        text: Number(root.value.toFixed(2)) + root.suffix
        color: Theme.textPrimary
        font.pixelSize: 12
    }
}
