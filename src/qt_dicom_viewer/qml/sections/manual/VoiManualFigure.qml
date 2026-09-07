pragma ComponentBehavior: Bound
import QtQuick

Canvas {
    id: figure
    objectName: "voiManualFigure"
    required property string chapter
    implicitHeight: 220
    onChapterChanged: requestPaint()
    onWidthChanged: requestPaint()
    onPaint: {
        const c = getContext("2d")
        c.reset()
        const scale = width / 760
        c.scale(scale, scale)
        c.fillStyle = "#111c26"
        c.fillRect(0, 0, 760, 220)
        c.lineWidth = 2
        function label(text, x, y, color) {
            c.fillStyle = color || "#c9d5df"
            c.font = "13px sans-serif"
            c.fillText(text, x, y)
        }
        function line(x1, y1, x2, y2, color) {
            c.strokeStyle = color
            c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke()
        }
        function ellipse(x, y, rx, ry, color) {
            c.save(); c.translate(x, y); c.scale(rx, ry)
            c.beginPath(); c.arc(0, 0, 1, 0, 2 * Math.PI)
            c.restore()
            c.fillStyle = "#333745"; c.fill()
            c.strokeStyle = color; c.stroke()
        }
        if (chapter === "segmentation") {
            c.strokeStyle = "#ed55ed"
            c.fillStyle = "#303040"
            c.fillRect(66, 80, 180, 100); c.strokeRect(66, 80, 180, 100)
            c.strokeRect(113, 43, 180, 100)
            line(66,80,113,43,"#ed55ed"); line(246,80,293,43,"#ed55ed")
            line(246,180,293,143,"#ed55ed")
            label("宽 32 mm", 118, 204)
            label("高 18 mm", 6, 129)
            label("深度 24 mm", 242, 35, "#62c9ec")
            label("自动深度 = √(宽 × 高)", 391, 78, "#62c9ec")
            label("调整宽高 → 深度一起更新", 391, 113)
            label("手动调深度 → 固定深度", 391, 145)
            label("切回自动 → 恢复尺寸跟随", 391, 177)
        } else if (chapter === "voi") {
            ellipse(118, 110, 67, 67, "#ed55ed")
            line(118,110,185,110,"#62c9ec")
            ellipse(118,110,3,3,"#62c9ec")
            label("按下：圆心", 75, 22)
            label("拖动：半径", 122, 102, "#62c9ec")
            label("直径 30 · 深度 30 → 球体", 32, 206)
            ellipse(385, 110, 67, 39, "#62c9ec")
            label("手动深度 18 → 椭球侧面", 300, 206)
            ellipse(625, 92, 61, 61, "#ed55ed")
            ellipse(625, 92, 33, 33, "#62c9ec")
            label("切面离开中心，截面变小", 540, 206)
        } else if (chapter === "quantification") {
            label("范围内原始体素", 38, 28)
            for (let i=0; i<12; ++i) {
                const h = 18 + ((i*37)%90)
                c.fillStyle = i >= 6 ? "#ed55ed" : "#526576"
                c.fillRect(40+i*22, 166-h, 17, h)
            }
            line(169,42,169,178,"#62c9ec")
            label("阈值", 152, 199, "#62c9ec")
            label("CT：HU ≥ 300", 368, 65, "#ed55ed")
            label("PET：SUV ≥ 2.5 / 可用活度单位", 368, 99, "#ed55ed")
            label("体积 = 选中体素数 × 体素体积", 368, 141)
            label("不使用屏幕亮度或 MIP 投影值统计", 368, 177)
        } else {
            c.fillStyle = "#263744"; c.fillRect(60, 37, 640, 46)
            label("◉    范围名称（双击编辑）                              × 删除这一项", 81, 65)
            c.strokeStyle = "#62c9ec"; c.strokeRect(60, 122, 310, 42)
            c.strokeRect(389, 122, 310, 42)
            label("清除分割 / 清除 VOI", 135, 148)
            label("全部清除 · 当前标签页", 454, 148)
            label("Esc 取消本次绘制或编辑    ·    Delete / Backspace 删除选中范围", 106, 204)
        }
    }
}
