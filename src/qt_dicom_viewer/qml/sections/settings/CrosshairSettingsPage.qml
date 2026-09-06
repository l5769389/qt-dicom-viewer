pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../center/viewportArea" as Views
import "../../theme"
ColumnLayout {
    id: root
    required property var settingsController
    readonly property var values: settingsController.values.crosshair
    spacing: 10
    Text { Layout.fillWidth: true; text: "每个切面的颜色和线宽同时用于另外两个视图中的参考线。"; color: Theme.textMuted; font.pixelSize: 12; wrapMode: Text.Wrap }
    Repeater {
        model: [{key: "axial", title: "AX · 轴位", horizontal: "coronal", vertical: "sagittal"},
                {key: "coronal", title: "COR · 冠状位", horizontal: "axial", vertical: "sagittal"},
                {key: "sagittal", title: "SAG · 矢状位", horizontal: "axial", vertical: "coronal"}]
        delegate: SettingsCard {
            id: card
            required property var modelData
            Layout.fillWidth: true
            Text { text: card.modelData.title; color: Theme.textPrimary; font.pixelSize: 14; font.bold: true }
            GridLayout {
                Layout.fillWidth: true
                columns: root.width > 450 ? 2 : 1
                uniformCellWidths: true
                columnSpacing: 16; rowSpacing: 10
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    spacing: 10
                    SettingColor {
                        Layout.fillWidth: true; title: "切面颜色"; settingName: "crosshair-" + card.modelData.key + "Color"
                        value: root.values[card.modelData.key + "Color"]
                        onEdited: color => root.settingsController.setValue("crosshair", card.modelData.key + "Color", color)
                    }
                    SettingSlider {
                        Layout.fillWidth: true; title: "线宽"; settingName: "crosshair-" + card.modelData.key + "Width"
                        value: root.values[card.modelData.key + "Width"]
                        onEdited: value => root.settingsController.setValue("crosshair", card.modelData.key + "Width", value)
                    }
                }
                Rectangle {
                    objectName: "crosshairPreview-" + card.modelData.key
                    Layout.minimumWidth: 0
                    Layout.fillWidth: true; Layout.preferredHeight: 100
                    color: Theme.canvasBackground; radius: 5
                    border.color: Theme.borderDefault
                    Views.CrosshairLayer {
                        anchors.fill: parent
                        crosshairPosition: Qt.point(width / 2, height / 2)
                        rotationDegrees: 0
                        crosshairStyle: ({centerGap: 14, lineWidth: 1,
                            horizontalWidth: root.values[card.modelData.horizontal + "Width"],
                            verticalWidth: root.values[card.modelData.vertical + "Width"],
                            horizontalColor: root.values[card.modelData.horizontal + "Color"],
                            verticalColor: root.values[card.modelData.vertical + "Color"]})
                    }
                    Text { anchors.left: parent.left; anchors.top: parent.top; anchors.margins: 10; text: card.modelData.title + " 预览"; color: Theme.textMuted; font.pixelSize: 11 }
                }
            }
        }
    }
}
