pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Shapes
import "../../../../theme"

Item {
    id: root
    property var preferences: ({})
    readonly property var styleSettings: preferences.measurement ?? ({})
    property bool draftStyle: isDraft
    readonly property bool dashed: draftStyle ? (styleSettings.editingDash ?? true) : (styleSettings.completedDash ?? false)
    required property var measurement
    required property var corners
    required property bool isDraft
    required property bool isSelected
    property bool showMetrics: true
    property string shortLabel: ""
    readonly property Item labelItem: showMetrics ? metricCard : compactLabel
    readonly property color lineColor: draftStyle ? (styleSettings.editingColor ?? Theme.measurementSelected) : (styleSettings.completedColor ?? Theme.measurementPrimary)

    readonly property string outlinePath: {
        if (root.corners.length !== 4)
            return ""
        const p = root.corners
        const xy = point => point.x + " " + point.y
        if (root.measurement.type === "rect")
            return "M " + xy(p[0]) + " L " + xy(p[1]) + " L " + xy(p[2]) + " L " + xy(p[3]) + " Z"
        // 用映射后的两条半轴构造贝塞尔椭圆，旋转/镜像/非等距像素均保持对齐。
        const cx = (p[0].x + p[2].x) / 2, cy = (p[0].y + p[2].y) / 2
        const ux = (p[1].x - p[0].x) / 2, uy = (p[1].y - p[0].y) / 2
        const vx = (p[3].x - p[0].x) / 2, vy = (p[3].y - p[0].y) / 2
        const point = (u, v) => (cx + u * ux + v * vx) + " " + (cy + u * uy + v * vy)
        const k = 0.5522847498
        return "M " + point(1, 0)
            + " C " + point(1, k) + " " + point(k, 1) + " " + point(0, 1)
            + " C " + point(-k, 1) + " " + point(-1, k) + " " + point(-1, 0)
            + " C " + point(-1, -k) + " " + point(-k, -1) + " " + point(0, -1)
            + " C " + point(k, -1) + " " + point(1, -k) + " " + point(1, 0) + " Z"
    }
    readonly property real rightEdge: corners.length ? Math.max(...corners.map(p => p.x)) : 0
    readonly property real leftEdge: corners.length ? Math.min(...corners.map(p => p.x)) : 0
    readonly property real topEdge: corners.length ? Math.min(...corners.map(p => p.y)) : 0

    Shape {
        preferredRendererType: Shape.CurveRenderer
        antialiasing: true
        anchors.fill: parent
        ShapePath {
            strokeColor: root.lineColor
            strokeWidth: root.styleSettings.lineWidth ?? 1.5
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            joinStyle: ShapePath.RoundJoin
            strokeStyle: root.dashed ? ShapePath.DashLine : ShapePath.SolidLine
            dashPattern: [4, 2]
            PathSvg { path: root.outlinePath }
        }
    }
    Repeater {
        model: root.corners
        Rectangle {
            required property var modelData
            width: 6; height: 6; radius: 1
            x: modelData.x - 3; y: modelData.y - 3
            visible: root.isDraft || root.isSelected
            color: Theme.panelBackground
            border.color: root.lineColor
            border.width: 1.5
        }
    }
    RoiMetricCard {
        id: metricCard
        objectName: "roiMetricCard"
        visible: root.showMetrics && root.corners.length === 4
        measurement: root.measurement
        accentColor: root.lineColor
        visibleMetrics: root.preferences.roi ?? ({})
        metricFontSize: root.styleSettings.fontSize ?? 13
        width: Math.max(0, Math.min(implicitWidth, root.width - 16))
        x: Math.max(8, Math.min(root.width - width - 8,
            root.rightEdge + width + 12 <= root.width ? root.rightEdge + 12 : root.leftEdge - width - 12))
        y: Math.max(8, Math.min(root.height - height - 8, root.topEdge))
    }
    Rectangle {
        id: compactLabel
        objectName: "mtfRoiMetricBadge"
        visible: !root.showMetrics && root.corners.length === 4 && root.shortLabel.length > 0
        implicitWidth: compactText.implicitWidth + 14
        width: Math.min(implicitWidth, Math.max(0, root.width - 8))
        implicitHeight: compactText.implicitHeight + 8
        x: Math.max(4, Math.min(root.width - width - 4,
            root.rightEdge + width + 8 <= root.width ? root.rightEdge + 8 : root.leftEdge - width - 8))
        y: Math.max(4, Math.min(root.height - height - 4, root.topEdge))
        color: "#e60d1722"
        border.width: 1
        border.color: root.lineColor
        radius: 4

        Text {
            id: compactText
            width: Math.max(0, compactLabel.width - 14)
            wrapMode: Text.Wrap
            objectName: "mtfRoiLabel"
            anchors.centerIn: parent
            text: root.shortLabel
            color: Theme.overlayText
            font.pixelSize: root.styleSettings.fontSize ?? 13
            font.weight: Font.DemiBold
            lineHeight: 1.2
        }
    }
}
