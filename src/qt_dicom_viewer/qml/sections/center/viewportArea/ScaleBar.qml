pragma ComponentBehavior: Bound
import QtQuick

Item {
    id: root
    objectName: "imageScaleBar"
    required property real pixelsPerMm
    required property bool calibrated
    required property var options
    readonly property real targetPixels: Math.min(120, width * 0.2)
    readonly property real lengthMm: {
        if (!calibrated || !Number.isFinite(pixelsPerMm) || pixelsPerMm <= 0 || targetPixels <= 0)
            return 0
        const target = targetPixels / pixelsPerMm
        const power = Math.pow(10, Math.floor(Math.log10(target)))
        const fraction = target / power
        return (fraction >= 5 ? 5 : fraction >= 2 ? 2 : 1) * power
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
        text: Number(root.lengthMm.toPrecision(3)) + " mm"
        color: line.color
        font.pixelSize: 11
        style: Text.Outline
        styleColor: "#aa000000"
    }
}
