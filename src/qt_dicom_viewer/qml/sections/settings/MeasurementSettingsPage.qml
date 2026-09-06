pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"
import "../center/viewportArea/measurementLayer" as Measurements
ColumnLayout {
    id: root
    required property var settingsController
    readonly property var values: settingsController.values.measurement
    spacing: 18
    SettingsCard {
        Layout.fillWidth: true
        Text { text: "测量样式"; color: Theme.textPrimary; font.pixelSize: 15; font.bold: true }
        GridLayout {
            Layout.fillWidth: true
            columns: root.width > 550 ? 2 : 1
            columnSpacing: 24; rowSpacing: 20
            SettingColor { Layout.fillWidth: true; title: "编辑 / 选中颜色"; settingName: "measurement-editingColor"; value: root.values.editingColor; onEdited: color => root.settingsController.setValue("measurement", "editingColor", color) }
            SettingColor { Layout.fillWidth: true; title: "完成后颜色"; settingName: "measurement-completedColor"; value: root.values.completedColor; onEdited: color => root.settingsController.setValue("measurement", "completedColor", color) }
            Components.AppCheckBox { objectName: "setting-measurement-editingDash"; text: "编辑 / 选中时使用虚线"; checked: root.values.editingDash; onClicked: root.settingsController.setValue("measurement", "editingDash", checked) }
            Components.AppCheckBox { objectName: "setting-measurement-completedDash"; text: "完成后使用虚线"; checked: root.values.completedDash; onClicked: root.settingsController.setValue("measurement", "completedDash", checked) }
            SettingSlider { Layout.fillWidth: true; title: "线宽"; settingName: "measurement-lineWidth"; value: root.values.lineWidth; onEdited: value => root.settingsController.setValue("measurement", "lineWidth", value) }
            SettingSlider { Layout.fillWidth: true; title: "文字大小"; settingName: "measurement-fontSize"; from: 10; to: 20; stepSize: 1; value: root.values.fontSize; onEdited: value => root.settingsController.setValue("measurement", "fontSize", value) }
        }
        Canvas {
            id: preview
            objectName: "measurementStylePreview"
            Layout.fillWidth: true; Layout.preferredHeight: 115
            property var options: root.values
            onOptionsChanged: requestPaint()
            onWidthChanged: requestPaint()
            onPaint: {
                const ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = Theme.canvasBackground; ctx.fillRect(0, 0, width, height)
                ;[{y: 38, color: options.editingColor, dashed: options.editingDash, label: "编辑 / 选中"},
                  {y: 85, color: options.completedColor, dashed: options.completedDash, label: "完成"}].forEach(row => {
                    ctx.strokeStyle = row.color; ctx.fillStyle = row.color; ctx.lineWidth = options.lineWidth
                    ctx.setLineDash(row.dashed ? [8, 5] : [])
                    ctx.beginPath(); ctx.moveTo(120, row.y); ctx.lineTo(width - 25, row.y); ctx.stroke()
                    ctx.font = options.fontSize + "px sans-serif"; ctx.fillText(row.label, 16, row.y + 4)
                })
            }
        }
    }
    SettingsCard {
        Layout.fillWidth: true
        Text { text: "箭头标注"; color: Theme.textPrimary; font.pixelSize: 15; font.bold: true }
        GridLayout {
            Layout.fillWidth: true
            columns: root.width > 550 ? 2 : 1
            columnSpacing: 24; rowSpacing: 18
            SettingColor { Layout.fillWidth: true; title: "箭头颜色"; settingName: "measurement-annotationColor"; value: root.values.annotationColor; onEdited: color => root.settingsController.setValue("measurement", "annotationColor", color) }
            SettingSlider { Layout.fillWidth: true; title: "箭头大小"; settingName: "measurement-annotationSize"; from: 8; to: 28; stepSize: 1; value: root.values.annotationSize; onEdited: value => root.settingsController.setValue("measurement", "annotationSize", value) }
        }
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 110
            color: Theme.canvasBackground; radius: 5
            Measurements.LengthMeasurementItem {
                anchors.fill: parent
                preferences: root.settingsController.values
                measurement: ({type: "arrow", label: ""})
                mappedPoints: [Qt.point(30, 75), Qt.point(width - 35, 35)]
                isDraft: false
                isSelected: false
            }
        }
        Text { Layout.fillWidth: true; text: "从右侧“标注”工具拖动绘制箭头。样式应用于全部视图；测量和标注内容仍按切片保存于当前会话。"; color: Theme.textMuted; font.pixelSize: 12; wrapMode: Text.Wrap }
    }
}
