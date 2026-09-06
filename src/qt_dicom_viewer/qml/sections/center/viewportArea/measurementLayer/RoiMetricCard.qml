pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../../../theme"

Rectangle {
    id: root
    property var visibleMetrics: ({})
    property int metricFontSize: 13
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
        {key: "area", label: "面积", value: format(metrics.area_mm2) + " mm²"},
        {key: "width", label: measurement.type === "ellipse" ? "横轴直径" : "宽度", value: format(metrics.width_mm) + " mm"},
        {key: "height", label: measurement.type === "ellipse" ? "纵轴直径" : "高度", value: format(metrics.height_mm) + " mm"},
        {key: "mean", label: "均值", value: format(metrics.mean) + unitSuffix},
        {key: "std", label: "标准差", value: format(metrics.std) + unitSuffix},
        {key: "minimum", label: "最小值", value: format(metrics.minimum) + unitSuffix},
        {key: "maximum", label: "最大值", value: format(metrics.maximum) + unitSuffix},
        {key: "count", label: "有效像素", value: String(metrics.pixel_count ?? 0)}
    ].concat(secondary ? [
        {key: "mean", label: "CT 均值", value: format(secondary.mean) + " HU"},
        {key: "std", label: "CT 标准差", value: format(secondary.std) + " HU"},
        {key: "minimum", label: "CT 最小值", value: format(secondary.minimum) + " HU"},
        {key: "maximum", label: "CT 最大值", value: format(secondary.maximum) + " HU"},
        {key: "count", label: "CT 有效像素", value: String(secondary.pixel_count ?? 0)}
    ] : []).filter(row => root.visibleMetrics[row.key] !== false)
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
                Text { text: metricRow.modelData.label; color: Theme.textMuted; font.pixelSize: root.metricFontSize - 2 }
                Text {
                    Layout.fillWidth: true
                    text: metricRow.modelData.value
                    color: Theme.overlayText
                    font.pixelSize: root.metricFontSize - 2
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
