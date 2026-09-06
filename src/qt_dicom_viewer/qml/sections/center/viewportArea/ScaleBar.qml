import QtQuick
import "../../../theme"

Item {
    id: scaleBar
    objectName: "viewportScaleBar"
    required property real pixelsPerMillimeter

    function niceLength(targetMillimeters) {
        const values = [1, 2, 5, 10, 20, 50, 100, 200, 500]
        let selected = values[0]
        for (const value of values) {
            if (value <= targetMillimeters)
                selected = value
        }
        return selected
    }

    readonly property real physicalLength: niceLength(
        110 / Math.max(pixelsPerMillimeter, 0.0001)
    )
    readonly property real barWidth: physicalLength * pixelsPerMillimeter
    readonly property string label: physicalLength >= 10
        ? (physicalLength / 10) + " cm"
        : physicalLength + " mm"

    width: Math.max(40, barWidth)
    height: 31

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        text: scaleBar.label
        color: Theme.overlayText
        font.pixelSize: 11
        font.weight: Font.DemiBold
        style: Text.Outline
        styleColor: Theme.overlayOutline
    }

    Item {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        width: scaleBar.barWidth
        height: 10

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 2
            color: Theme.overlayText
        }
        Rectangle {
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            width: 2
            height: parent.height
            color: Theme.overlayText
        }
        Rectangle {
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            width: 2
            height: parent.height
            color: Theme.overlayText
        }
    }
}
