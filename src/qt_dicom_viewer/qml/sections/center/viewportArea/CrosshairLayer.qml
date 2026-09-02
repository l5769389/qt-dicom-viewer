import QtQuick

Item {
    id: root
    clip: true

    required property var crosshairStyle
    required property point crosshairPosition
    required property real rotationDegrees
    property real centerX: root.crosshairPosition.x
    property real centerY: root.crosshairPosition.y

    property real centerGap: root.crosshairStyle.centerGap
    property real lineWidth: root.crosshairStyle.lineWidth
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
            y: root.centerY - root.lineWidth / 2
            width: root.armLength
            height: root.lineWidth
            color: root.horizontalColor
        }

        Rectangle {
            x: root.centerX + root.centerGap / 2
            y: root.centerY - root.lineWidth / 2
            width: root.armLength
            height: root.lineWidth
            color: root.horizontalColor
        }

        Rectangle {
            x: root.centerX - root.lineWidth / 2
            y: root.centerY - root.centerGap / 2 - root.armLength
            width: root.lineWidth
            height: root.armLength
            color: root.verticalColor
        }

        Rectangle {
            x: root.centerX - root.lineWidth / 2
            y: root.centerY + root.centerGap / 2
            width: root.lineWidth
            height: root.armLength
            color: root.verticalColor
        }
    }
}
