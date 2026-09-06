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
    Text { Layout.fillWidth: true; text: root.title; color: Theme.textSecondary; font.pixelSize: 12; wrapMode: Text.Wrap }
    Components.AppSlider {
        objectName: "setting-" + root.settingName
        Layout.preferredWidth: Math.min(140, root.width * 0.32)
        visible: root.width >= 320
        from: root.from; to: root.to; stepSize: root.stepSize
        value: root.value; Accessible.name: root.title
        onMoved: root.edited(value)
    }
    Components.AppTextField {
        objectName: "settingInput-" + root.settingName
        Layout.preferredWidth: 60
        horizontalAlignment: Text.AlignRight
        text: Number(root.value.toFixed(2))
        Accessible.name: root.title
        validator: DoubleValidator { locale: "C"; bottom: root.from; top: root.to; decimals: 2 }
        onActiveFocusChanged: {
            if (!activeFocus && !acceptableInput) text = Qt.binding(() => Number(root.value.toFixed(2)))
        }
        onEditingFinished: {
            const number = Number(text)
            if (text.trim() && Number.isFinite(number) && number >= root.from && number <= root.to)
                root.edited(number)
            text = Qt.binding(() => Number(root.value.toFixed(2)))
        }
    }
    Text { Layout.preferredWidth: 20; text: root.suffix.trim(); color: Theme.textMuted; font.pixelSize: 11 }
}
