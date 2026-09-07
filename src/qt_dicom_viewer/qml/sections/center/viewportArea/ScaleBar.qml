pragma ComponentBehavior: Bound
import QtQuick

Item {
    id: root
    objectName: "imageScaleBar"
    required property real pixelsPerMm
    required property bool calibrated
    required property var options
    readonly property real availablePixels: Math.max(0, width - 32)
    readonly property real lengthMm: {
        if (!calibrated || !Number.isFinite(pixelsPerMm) || pixelsPerMm <= 0)
            return 0
        const selected = options.lengthMm ?? 100
        const choices = [100, 50, 20, 10, 1]
        return choices.find(mm => mm <= selected && mm * pixelsPerMm <= availablePixels) ?? 0
    }
    readonly property real barPixels: lengthMm * pixelsPerMm
    visible: options.enabled !== false && lengthMm > 0
    height: 28
    Rectangle {
        id: line
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        width: root.barPixels
        height: 1
        color: root.options.color ?? "#f8fafc"
        Rectangle { width: 1; height: 7; anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter; color: line.color }
        Rectangle { width: 1; height: 7; anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; color: line.color }
    }
    Text {
        objectName: "scaleBarLabel"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: line.top
        anchors.bottomMargin: 5
        text: root.lengthMm === 100 ? "10 cm" : root.lengthMm + " mm"
        color: line.color
        font.pixelSize: 11
        style: Text.Outline
        styleColor: "#aa000000"
    }
}
