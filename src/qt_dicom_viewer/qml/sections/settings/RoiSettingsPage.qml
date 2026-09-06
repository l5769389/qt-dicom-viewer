pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "../center/viewportArea/measurementLayer" as Measurement
import "../../theme"
ColumnLayout {
    id: root
    required property var settingsController
    spacing: 18
    SettingsCard {
        Layout.fillWidth: true
        Text { text: "ROI 显示指标"; color: Theme.textPrimary; font.pixelSize: 15; font.bold: true }
        Text { Layout.fillWidth: true; text: "用于矩形与椭圆 ROI。修改只影响信息卡的显示，不改变计算结果。"; color: Theme.textMuted; font.pixelSize: 12; wrapMode: Text.Wrap }
        GridLayout {
            Layout.fillWidth: true
            columns: root.width > 500 ? 2 : 1
            columnSpacing: 20; rowSpacing: 12
            Repeater {
                model: root.settingsController.roiFields
                delegate: Components.AppCheckBox {
                    required property var modelData
                    objectName: "setting-roi-" + modelData.key
                    Layout.fillWidth: true
                    text: modelData.label
                    checked: root.settingsController.values.roi[modelData.key]
                    onClicked: root.settingsController.setValue("roi", modelData.key, checked)
                }
            }
        }
    }
    Text { text: "信息卡预览"; color: Theme.textMuted; font.pixelSize: 12 }
    Measurement.RoiMetricCard {
        Layout.preferredWidth: 260
        accentColor: root.settingsController.values.measurement.completedColor
        visibleMetrics: root.settingsController.values.roi
        metricFontSize: root.settingsController.values.measurement.fontSize
        measurement: ({type: "rect", label: "矩形 ROI", metrics: {area_mm2: 400, width_mm: 20, height_mm: 20, mean: 40, std: 8.5, minimum: 12, maximum: 65, pixel_count: 400, unit: "HU"}})
    }
}
