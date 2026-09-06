pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../../theme"

ColumnLayout {
    spacing: 12
    Text { text: "箭头标注"; color: Theme.textPrimary; font.pixelSize: 14; font.bold: true }
    Text {
        Layout.fillWidth: true
        text: "拖动绘制箭头，终点为箭头尖端。\n选中后可移动或调整端点。\nDelete 删除，Esc 取消。"
        color: Theme.textMuted
        font.pixelSize: 12
        lineHeight: 1.5
        wrapMode: Text.Wrap
    }
    Text {
        Layout.fillWidth: true
        text: "样式在设置 → 测量与标注中调整。标注保留在当前切片和会话。"
        color: Theme.textSubtle
        font.pixelSize: 11
        wrapMode: Text.Wrap
    }
    Item { Layout.fillHeight: true }
}
