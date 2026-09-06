pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../center/viewportArea" as Views
import "../../theme"
SettingsSplit {
    id: root
    required property var settingsController
    readonly property var values: settingsController.values.crosshair
    readonly property var planes: [{key: "axial", title: "AX · 轴位", horizontal: "coronal", vertical: "sagittal"}, {key: "coronal", title: "COR · 冠状位", horizontal: "axial", vertical: "sagittal"}, {key: "sagittal", title: "SAG · 矢状位", horizontal: "axial", vertical: "coronal"}]
    Repeater {
        model: root.planes
        delegate: SettingsSection {
            id: section
            required property var modelData
            Layout.fillWidth: true
            title: modelData.title
            SettingColor { Layout.fillWidth: true; title: "切面颜色"; settingName: "crosshair-" + section.modelData.key + "Color"; value: root.values[section.modelData.key + "Color"]; onEdited: color => root.settingsController.setValue("crosshair", section.modelData.key + "Color", color) }
            SettingSlider { Layout.fillWidth: true; title: "线宽"; settingName: "crosshair-" + section.modelData.key + "Width"; value: root.values[section.modelData.key + "Width"]; onEdited: value => root.settingsController.setValue("crosshair", section.modelData.key + "Width", value) }
        }
    }
    preview: Component {
        ColumnLayout {
            spacing: 10
            Text { text: "参考线预览"; color: Theme.textMuted; font.pixelSize: 12 }
            Repeater {
                model: root.planes
                delegate: Rectangle {
                    id: card
                    required property var modelData
                    objectName: "crosshairPreview-" + modelData.key
                    Layout.fillWidth: true; Layout.preferredHeight: 100
                    color: Theme.canvasBackground; radius: 4
                    Views.CrosshairLayer {
                        anchors.fill: parent
                        crosshairPosition: Qt.point(width / 2, height / 2 + 8)
                        rotationDegrees: 0
                        crosshairStyle: ({centerGap: 14, lineWidth: 1, horizontalWidth: root.values[card.modelData.horizontal + "Width"], verticalWidth: root.values[card.modelData.vertical + "Width"], horizontalColor: root.values[card.modelData.horizontal + "Color"], verticalColor: root.values[card.modelData.vertical + "Color"]})
                    }
                    Text { anchors.left: parent.left; anchors.top: parent.top; anchors.margins: 10; text: card.modelData.title; color: Theme.textMuted; font.pixelSize: 11 }
                }
            }
            Text { Layout.fillWidth: true; text: "切面颜色与线宽用于另外两个视图中的参考线。"; color: Theme.textMuted; font.pixelSize: 11; wrapMode: Text.Wrap }
        }
    }
}
