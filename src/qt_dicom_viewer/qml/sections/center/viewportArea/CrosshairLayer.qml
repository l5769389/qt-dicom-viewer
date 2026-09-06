import QtQuick

Item {
    id: root
    objectName: "mprCrosshairLayer"
    clip: true

    required property var crosshairStyle
    required property point crosshairPosition
    required property real rotationDegrees
    property real centerX: root.crosshairPosition.x
    property real centerY: root.crosshairPosition.y

    property real centerGap: root.crosshairStyle.centerGap
    property real lineWidth: root.crosshairStyle.lineWidth
    property real horizontalWidth: root.crosshairStyle.horizontalWidth ?? lineWidth
    property real verticalWidth: root.crosshairStyle.verticalWidth ?? lineWidth
    property color horizontalColor: root.crosshairStyle.horizontalColor
    property color verticalColor: root.crosshairStyle.verticalColor
    property real armLength: 2 * Math.hypot(root.width, root.height)

    Item {
        anchors.fill: parent

        transform: Rotation {
            origin.x: root.centerX
            origin.y: root.centerY
            angle: root.rotationDegrees
        }

        Rectangle {
            x: root.centerX - root.centerGap / 2 - root.armLength
            y: root.centerY - root.horizontalWidth / 2
            width: root.armLength
            height: root.horizontalWidth
            color: root.horizontalColor
        }

        Rectangle {
            x: root.centerX + root.centerGap / 2
            y: root.centerY - root.horizontalWidth / 2
            width: root.armLength
            height: root.horizontalWidth
            color: root.horizontalColor
        }

        Rectangle {
            x: root.centerX - root.verticalWidth / 2
            y: root.centerY - root.centerGap / 2 - root.armLength
            width: root.verticalWidth
            height: root.armLength
            color: root.verticalColor
        }

        Rectangle {
            x: root.centerX - root.verticalWidth / 2
            y: root.centerY + root.centerGap / 2
            width: root.verticalWidth
            height: root.armLength
            color: root.verticalColor
        }
    }
}
