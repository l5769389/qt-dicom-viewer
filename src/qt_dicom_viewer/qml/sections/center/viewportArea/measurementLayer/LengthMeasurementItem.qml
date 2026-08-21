import QtQuick
import QtQuick.Shapes

Item {
    id: root

    required property var measurement

    required property var isDraft

    readonly property real startX:
        Number(measurement.startColumn ?? 0) + 0.5

    readonly property real startY:
        Number(measurement.startRow ?? 0) + 0.5

    readonly property real endX:
        Number(measurement.endColumn ?? 0) + 0.5

    readonly property real endY:
        Number(measurement.endRow ?? 0) + 0.5

    Shape {
        anchors.fill: parent

        ShapePath {
            strokeColor: root.isDraft ? 'green' : "#ffd43b"
            strokeWidth: 1.5
            fillColor: "transparent"

            startX: root.startX
            startY: root.startY

            PathLine {
                x: root.endX
                y: root.endY
            }
        }
    }

    Rectangle {
        width: 5
        height: 5
        radius: width / 2
        color: root.isDraft ? 'green' : "#ffd43b"
        visible: root.isDraft
        x: root.startX - width / 2
        y: root.startY - height / 2
    }

    Rectangle {
        width: 5
        height: 5
        radius: width / 2
        color: root.isDraft ? 'green' : "#ffd43b"
        visible: root.isDraft
        x: root.endX - width / 2
        y: root.endY - height / 2
    }

    Text {
        x: (root.startX + root.endX) / 2 + 6
        y: (root.startY + root.endY) / 2 - height - 4

        text: measurement.label ?? "--"
        color: root.isDraft ? 'green' : "#ffd43b"
        font.pixelSize: 13
        font.bold: true

        style: Text.Outline
        styleColor: "#80000000"
    }
}