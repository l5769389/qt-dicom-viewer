// CrosshairLayer.qml
import QtQuick

Item {
    id: root

    required property var crosshairStyle
required property point crosshairPosition
    property real centerX: root.crosshairPosition.x
    property real centerY: root.crosshairPosition.y

    property real centerGap: root.crosshairStyle.centerGap
    property real lineWidth: root.crosshairStyle.lineWidth
    property color horizontalColor: root.crosshairStyle.horizontalColor
    property color verticalColor: root.crosshairStyle.verticalColor

    // 左侧横线
    Rectangle {
        x: 0
        y: root.centerY - root.lineWidth / 2
        width: Math.max(0, root.centerX - root.centerGap / 2)
        height: root.lineWidth
        color: root.horizontalColor
    }

    // 右侧横线
    Rectangle {
        x: root.centerX + root.centerGap / 2
        y: root.centerY - root.lineWidth / 2
        width: Math.max(
            0,
            root.width - root.centerX - root.centerGap / 2
        )
        height: root.lineWidth
        color: root.horizontalColor
    }

    // 上方竖线
    Rectangle {
        x: root.centerX - root.lineWidth / 2
        y: 0
        width: root.lineWidth
        height: Math.max(0, root.centerY - root.centerGap / 2)
        color: root.verticalColor
    }

    // 下方竖线
    Rectangle {
        x: root.centerX - root.lineWidth / 2
        y: root.centerY + root.centerGap / 2
        width: root.lineWidth
        height: Math.max(
            0,
            root.height - root.centerY - root.centerGap / 2
        )
        color: root.verticalColor
    }
}