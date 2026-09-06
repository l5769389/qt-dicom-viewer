pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../../../theme"

Rectangle {
    id: root
    required property var measurement
    required property color accentColor
    readonly property var metrics: measurement.metrics ?? ({})
    readonly property var secondary: measurement.secondaryMetrics ?? null
    readonly property string unitSuffix: metrics.unit ? " " + metrics.unit : ""
    function format(value) {
        if (typeof value !== "number" || !Number.isFinite(value))
            return "—"
        const unit = String(metrics.unit ?? "")
        const isPetUnit = unit.indexOf("SUV") === 0
            || unit.indexOf("Bq/ml") >= 0
        if (!isPetUnit)
            return value.toFixed(1)
        return value.toFixed(Math.abs(value) < 1 ? 3 : 2)
    }
    readonly property var rows: [
        {label: "面积", value: format(metrics.area_mm2) + " mm²"},
        {label: measurement.type === "ellipse" ? "轴径" : "宽 × 高",
            value: format(metrics.width_mm) + " × " + format(metrics.height_mm) + " mm"},
        {label: "均值", value: format(metrics.mean) + unitSuffix},
        {label: "标准差", value: format(metrics.std) + unitSuffix},
        {label: "最小 / 最大", value: format(metrics.minimum) + " / " + format(metrics.maximum) + unitSuffix},
        {label: "有效像素", value: String(metrics.pixel_count ?? 0)}
    ].concat(secondary ? [
        {label: "CT 均值 / 标准差", value: format(secondary.mean) + " / " + format(secondary.std) + " HU"},
        {label: "CT 最小 / 最大", value: format(secondary.minimum) + " / " + format(secondary.maximum) + " HU"},
        {label: "CT 有效像素", value: String(secondary.pixel_count ?? 0)}
    ] : [])
    implicitWidth: 238
    implicitHeight: content.implicitHeight + 20
    height: implicitHeight
    radius: 6
    color: Qt.rgba(0.035, 0.065, 0.095, 0.92)
    border.width: 1
    border.color: Qt.rgba(accentColor.r, accentColor.g, accentColor.b, 0.55)

    ColumnLayout {
        id: content
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 10
        spacing: 5
        Text {
            text: root.measurement.label ?? "ROI"
            color: root.accentColor
            font.pixelSize: 12
            font.weight: Font.DemiBold
        }
        Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: Theme.dividerColor }
        Repeater {
            model: root.rows
            RowLayout {
                id: metricRow
                required property var modelData
                Layout.fillWidth: true
                spacing: 8
                Text { text: metricRow.modelData.label; color: Theme.textMuted; font.pixelSize: 11 }
                Text {
                    Layout.fillWidth: true
                    text: metricRow.modelData.value
                    color: Theme.overlayText
                    font.pixelSize: 11
                    horizontalAlignment: Text.AlignRight
                    elide: Text.ElideRight
                }
            }
        }
        // Text {
        //     Layout.fillWidth: true
        //     text: root.metrics.pixel_count > 0 ? "仅统计影像内有效像素" : "区域内无有效像素"
        //     color: Theme.textMuted
        //     font.pixelSize: 10
        //     wrapMode: Text.Wrap
        // }
    }
}
