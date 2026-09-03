import QtQuick
import QtQuick.Shapes
import "../../../../theme"

Item {
    id: root

    required property var measurement

    required property var isDraft
    required property bool isSelected
    property alias labelItem: measurementLabel
    property var mappedPoints: [
        Qt.point(Number(measurement.startColumn ?? 0) + 0.5, Number(measurement.startRow ?? 0) + 0.5),
        Qt.point(Number(measurement.endColumn ?? 0) + 0.5, Number(measurement.endRow ?? 0) + 0.5)
    ]

    readonly property color measurementColor:
        isDraft || isSelected
            ? Theme.measurementSelected
            : Theme.measurementPrimary

    readonly property real startX:
        mappedPoints.length > 0 ? mappedPoints[0].x : 0

    readonly property real startY:
        mappedPoints.length > 0 ? mappedPoints[0].y : 0

    readonly property real endX:
        mappedPoints.length > 1 ? mappedPoints[1].x : 0

    readonly property real endY:
        mappedPoints.length > 1 ? mappedPoints[1].y : 0

    Shape {
        anchors.fill: parent

        ShapePath {
            strokeColor: root.measurementColor
            strokeWidth: 1.5
            fillColor: "transparent"
            strokeStyle: root.isDraft
                ? ShapePath.DashLine
                : ShapePath.SolidLine
            dashPattern: [4, 2]
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
        color:  root.measurementColor
        visible: root.isDraft || root.isSelected
        x: root.startX - width / 2
        y: root.startY - height / 2
    }

    Rectangle {
        width: 5
        height: 5
        radius: width / 2
        color:  root.measurementColor
        visible: root.isDraft || root.isSelected
        x: root.endX - width / 2
        y: root.endY - height / 2
    }

    Text {
        id: measurementLabel
        objectName: "measurementLabel"
        x: (root.startX + root.endX) / 2 + 6
        y: (root.startY + root.endY) / 2 - height - 4

        text: root.measurement.label ?? "--"
        color:  root.measurementColor
        font.pixelSize: 13
        font.bold: true

        style: Text.Outline
        styleColor: Theme.overlayOutline
    }
}
