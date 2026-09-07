pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import "../../../theme"

Canvas {
    id: chart
    objectName: "mtfChart"
    property var result: ({})
    readonly property color xColor: "#41cce5"
    readonly property color yColor: "#f6bf66"
    property bool showX: true
    property bool showY: true
    implicitHeight: 238
    onResultChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onShowXChanged: requestPaint()
    onShowYChanged: requestPaint()

    // 两行紧凑图例放在图表右上方的留白内，不遮挡高于 1 的曲线。
    Column {
        id: legend
        objectName: "mtfChartLegend"
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.rightMargin: 12
        spacing: 3
        Row {
            anchors.right: parent.right
            spacing: 4
            Basic.Button {
                id: xLegend
                objectName: "mtfLegend-x"
                implicitWidth: 43
                implicitHeight: 20
                hoverEnabled: true
                onClicked: chart.showX = !chart.showX
                contentItem: Text {
                    text: "━ X"
                    color: chart.xColor
                    opacity: chart.showX ? 1 : 0.35
                    font.pixelSize: 11
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 4
                    color: xLegend.hovered ? Theme.controlHover : "transparent"
                    border.width: xLegend.visualFocus ? 1 : 0
                    border.color: Theme.focusBorder
                }
                Basic.ToolTip.visible: hovered
                Basic.ToolTip.delay: 600
                Basic.ToolTip.timeout: 2000
                Basic.ToolTip.text: chart.showX ? "隐藏 X 曲线" : "显示 X 曲线"
            }
            Basic.Button {
                id: yLegend
                objectName: "mtfLegend-y"
                implicitWidth: 43
                implicitHeight: 20
                hoverEnabled: true
                onClicked: chart.showY = !chart.showY
                contentItem: Text {
                    text: "┄ Y"
                    color: chart.yColor
                    opacity: chart.showY ? 1 : 0.35
                    font.pixelSize: 11
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 4
                    color: yLegend.hovered ? Theme.controlHover : "transparent"
                    border.width: yLegend.visualFocus ? 1 : 0
                    border.color: Theme.focusBorder
                }
                Basic.ToolTip.visible: hovered
                Basic.ToolTip.delay: 600
                Basic.ToolTip.timeout: 2000
                Basic.ToolTip.text: chart.showY ? "隐藏 Y 曲线" : "显示 Y 曲线"
            }
        }
        Text {
            objectName: "mtfThresholdLegend"
            text: "● MTF50    ◆ MTF10"
            color: Theme.textMuted
            font.pixelSize: 11
        }
    }

    onPaint: {
        const ctx = getContext("2d")
        ctx.reset()
        if (!result.x || !result.y || width < 100)
            return
        const axes = [result.x, result.y]
        const colors = [xColor.toString(), yColor.toString()]
        const left = 35, top = Math.max(31, legend.height + 8), w = width - left - 12, h = height - top - 43
        const xmax = Math.max(...axes.map(a => a.frequency[a.frequency.length - 1]))
        let ymax = 1.05
        for (const axis of axes)
            for (const value of axis.mtf)
                ymax = Math.max(ymax, value * 1.05)
        const px = f => left + f / xmax * w
        const py = v => top + h * (1 - v / ymax)
        ctx.font = "11px sans-serif"
        ctx.textBaseline = "middle"
        ctx.fillStyle = Theme.textMuted.toString()
        ctx.fillText("MTF", 1, 11)
        for (const value of [0, 0.1, 0.5, 1]) {
            ctx.strokeStyle = "#263541"
            ctx.lineWidth = 1
            ctx.beginPath(); ctx.moveTo(left, py(value)); ctx.lineTo(left + w, py(value)); ctx.stroke()
            ctx.fillStyle = Theme.textMuted.toString()
            // 响应明显大于 1 时，避免零刻度与 0.1 参考线文字重叠。
            if (value !== 0 || h * 0.1 / ymax >= 12) {
                ctx.textAlign = "right"; ctx.fillText(value.toFixed(1), left - 6, py(value))
            }
        }
        if (ymax > 1.15) {
            ctx.fillText(ymax.toFixed(1), left - 6, top)
        }
        ctx.strokeStyle = "#647687"
        ctx.beginPath(); ctx.moveTo(left, top); ctx.lineTo(left, top + h); ctx.lineTo(left + w, top + h); ctx.stroke()
        for (let tick = 0; tick <= 4; ++tick) {
            const value = tick * xmax / 4
            ctx.textAlign = tick === 4 ? "right" : "center"
            ctx.fillStyle = Theme.textMuted.toString()
            ctx.fillText(value.toFixed(2), px(value), top + h + 14)
        }
        ctx.textAlign = "center"
        ctx.fillText("空间频率 (lp/mm)", left + w / 2, height - 7)
        for (let direction = 0; direction < 2; ++direction) {
            if ((direction === 0 && !showX) || (direction === 1 && !showY))
                continue
            const axis = axes[direction]
            ctx.strokeStyle = colors[direction]; ctx.lineWidth = 1.8
            ctx.beginPath()
            // Canvas 无需 QtCharts；Y 使用分段虚线，颜色之外仍可辨认方向。
            for (let i = 0; i < axis.mtf.length; ++i) {
                const x = px(axis.frequency[i]), y = py(axis.mtf[i])
                if (i === 0 || (direction === 1 && Math.floor(i / 3) % 2 === 1))
                    ctx.moveTo(x, y)
                else
                    ctx.lineTo(x, y)
            }
            ctx.stroke()
            for (const marker of [{frequency: axis.mtf50, value: 0.5}, {frequency: axis.mtf10, value: 0.1}]) {
                if (marker.frequency === null || marker.frequency === undefined)
                    continue
                const x = px(marker.frequency), y = py(marker.value)
                ctx.fillStyle = colors[direction]
                ctx.beginPath()
                if (marker.value === 0.5)
                    ctx.arc(x, y, 3.5, 0, Math.PI * 2)
                else {
                    ctx.moveTo(x, y - 4); ctx.lineTo(x + 4, y); ctx.lineTo(x, y + 4); ctx.lineTo(x - 4, y); ctx.closePath()
                }
                ctx.fill()
            }
        }
    }
}
