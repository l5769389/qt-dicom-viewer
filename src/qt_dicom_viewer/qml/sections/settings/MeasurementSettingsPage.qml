pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"
import "../center/viewportArea/measurementLayer" as Measurements

SettingsSplit {
    id: root
    required property var settingsController
    readonly property var values: settingsController.values.measurement
    SettingsSection {
        Layout.fillWidth: true
        title: "测量线条"
        description: "选中时使用编辑样式，取消选中后使用完成样式。"
        SettingColor { Layout.fillWidth: true; title: "编辑 / 选中"; settingName: "measurement-editingColor"; value: root.values.editingColor; onEdited: color => root.settingsController.setValue("measurement", "editingColor", color) }
        Components.AppCheckBox { objectName: "setting-measurement-editingDash"; text: "选中时使用虚线"; checked: root.values.editingDash; onClicked: root.settingsController.setValue("measurement", "editingDash", checked) }
        SettingColor { Layout.fillWidth: true; title: "完成后"; settingName: "measurement-completedColor"; value: root.values.completedColor; onEdited: color => root.settingsController.setValue("measurement", "completedColor", color) }
        Components.AppCheckBox { objectName: "setting-measurement-completedDash"; text: "完成后使用虚线"; checked: root.values.completedDash; onClicked: root.settingsController.setValue("measurement", "completedDash", checked) }
        SettingSlider { Layout.fillWidth: true; title: "线宽"; settingName: "measurement-lineWidth"; value: root.values.lineWidth; onEdited: value => root.settingsController.setValue("measurement", "lineWidth", value) }
        SettingSlider { Layout.fillWidth: true; title: "文字大小"; settingName: "measurement-fontSize"; from: 10; to: 20; stepSize: 1; value: root.values.fontSize; onEdited: value => root.settingsController.setValue("measurement", "fontSize", value) }
    }
    SettingsSection {
        Layout.fillWidth: true
        title: "箭头标注"
        SettingColor { Layout.fillWidth: true; title: "箭头颜色"; settingName: "measurement-annotationColor"; value: root.values.annotationColor; onEdited: color => root.settingsController.setValue("measurement", "annotationColor", color) }
        SettingSlider { Layout.fillWidth: true; title: "箭头头部大小"; settingName: "measurement-annotationSize"; from: 8; to: 28; stepSize: 1; value: root.values.annotationSize; onEdited: value => root.settingsController.setValue("measurement", "annotationSize", value) }
    }
    preview: Component {
        ColumnLayout {
            spacing: 10
            Text { text: "样式预览"; color: Theme.textMuted; font.pixelSize: 12 }
            Canvas {
                id: preview
                objectName: "measurementStylePreview"
                Layout.fillWidth: true; Layout.preferredHeight: 180
                property var options: root.values
                onOptionsChanged: requestPaint()
                onWidthChanged: requestPaint()
                onPaint: {
                    const ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    ctx.fillStyle = Theme.canvasBackground; ctx.fillRect(0, 0, width, height)
                    ;[{y: 62, color: options.editingColor, dash: options.editingDash, label: "编辑 / 选中"},
                      {y: 140, color: options.completedColor, dash: options.completedDash, label: "完成"}].forEach(row => {
                        ctx.font = "11px sans-serif"; ctx.fillStyle = Theme.textMuted; ctx.fillText(row.label, 16, row.y - 30)
                        ctx.strokeStyle = row.color; ctx.fillStyle = row.color; ctx.lineWidth = options.lineWidth
                        ctx.setLineDash(row.dash ? [6, 4] : [])
                        ctx.beginPath(); ctx.moveTo(22, row.y); ctx.lineTo(width - 22, row.y); ctx.stroke()
                        ctx.setLineDash([])
                        ;[22, width - 22].forEach(x => { ctx.beginPath(); ctx.arc(x, row.y, 3, 0, Math.PI * 2); ctx.fill() })
                        ctx.font = options.fontSize + "px sans-serif"; ctx.textAlign = "center"
                        ctx.fillText("32.4 mm", width / 2, row.y - 9); ctx.textAlign = "left"
                    })
                }
            }
            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 100
                color: Theme.canvasBackground; radius: 4
                Measurements.LengthMeasurementItem {
                    anchors.fill: parent; preferences: root.settingsController.values
                    measurement: ({type: "arrow", label: ""})
                    mappedPoints: [Qt.point(28, 72), Qt.point(width - 30, 30)]
                    isDraft: false; isSelected: false
                }
                Text { anchors.left: parent.left; anchors.top: parent.top; anchors.margins: 12; text: "箭头"; color: Theme.textMuted; font.pixelSize: 11 }
            }
            Text { Layout.fillWidth: true; text: "样式应用于所有视图。测量与标注内容按切片保存。"; color: Theme.textMuted; font.pixelSize: 11; wrapMode: Text.Wrap }
        }
    }
}
