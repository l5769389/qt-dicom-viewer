pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../../components" as Components
import "../../../theme"

ColumnLayout {
    id: panel
    objectName: "fusionBlendPanel"
    required property var controller
    spacing: 12
    Text { text: "融合比例"; color: Theme.textPrimary; font.pixelSize: 14; font.bold: true }
    Text {
        Layout.fillWidth: true
        text: "调整融合格中 PET 的叠加比例，观察代谢热点与 CT 解剖结构的位置关系。"
        color: Theme.textMuted
        font.pixelSize: 12
        wrapMode: Text.Wrap
    }
    RowLayout {
        Layout.fillWidth: true
        Text { Layout.fillWidth: true; text: "PET 叠加"; color: Theme.textPrimary }
        Components.AppNumberField {
            objectName: "fusionOpacityInput"
            Layout.preferredWidth: 80
            numberValue: panel.controller.opacity * 100
            minimum: 0; maximum: 100; decimals: 0
            onEdited: value => panel.controller.setOpacity(value / 100)
        }
        Text { text: "%"; color: Theme.textMuted }
    }
    Components.AppSlider {
        objectName: "fusionOpacity"
        Layout.fillWidth: true
        from: 0; to: 1; stepSize: 0.01
        value: panel.controller.opacity
        onMoved: panel.controller.setOpacity(value)
    }
    RowLayout {
        Layout.fillWidth: true
        Text { text: "CT"; color: Theme.textMuted; font.pixelSize: 11 }
        Item { Layout.fillWidth: true }
        Text { text: "PET"; color: Theme.textMuted; font.pixelSize: 11 }
    }
    RowLayout {
        Layout.fillWidth: true
        Repeater {
            model: [0, 25, 50, 75, 100]
            delegate: Components.AppButton {
                required property int modelData
                objectName: "fusionOpacity-" + modelData
                Layout.fillWidth: true
                text: modelData + "%"
                compact: true
                checkable: true
                checked: Math.round(panel.controller.opacity * 100) === modelData
                onClicked: panel.controller.setOpacity(modelData / 100)
            }
        }
    }
}
