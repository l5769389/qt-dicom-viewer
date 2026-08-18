import QtQuick
import QtQuick.Layouts

pragma
ComponentBehavior: Bound

Item {
    id: viewportOverlay
    required property var activeViewport
    readonly property int overlayMargin: 2
    readonly property var overlay: activeViewport ? activeViewport.overlayInfo : ({})
    readonly property var cursorInfo: activeViewport ? activeViewport.cursorInfo : ({})


    component OverlayText: Text {
        visible: viewportOverlay.activeViewport !== null
        color: "#f2f5f8"
        font.pixelSize: 12
        font.weight: Font.DemiBold
        font.letterSpacing: 0.15
        lineHeight: 1.28
        style: Text.Outline
        styleColor: "#cc000000"
        wrapMode: Text.Wrap
        z: 2
    }

    function overlayValue(key) {
        const value = overlay[key]
        return value === undefined || value === null || value === ""
            ? "--" : value
    }

    function cursorValue(key) {
        const value = cursorInfo[key]
        return value === undefined || value === null || value === ""
            ? "--" : value
    }

    OverlayText {
        id: topLeftText
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.margins: viewportOverlay.overlayMargin
        width: Math.min(implicitWidth, viewportOverlay.width * 0.46)
        text: overlayValue("manufacturer")
            + "\n" + overlayValue("seriesDescription")
            + "\nLocation: "
            + overlayValue("sliceLocation")
            + "\nSlice: "
            + overlayValue("sliceIndex")
            + " / " + overlayValue("sliceCount")
    }

    OverlayText {
        id: topRightText
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: viewportOverlay.overlayMargin
        width: Math.min(implicitWidth, viewportOverlay.width * 0.46)
        horizontalAlignment: Text.AlignRight
        text: "Patient: " + overlayValue("patientName")
            + "\nID: " + overlayValue("patientId")
    }

    OverlayText {
        id: bottomLeftText
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: viewportOverlay.overlayMargin
        width: Math.min(implicitWidth, viewportOverlay.width * 0.46)
        text: "kV: " + overlayValue("kvp")
            + "   mA: " + overlayValue("tubeCurrentMa")
            + "\nThickness: "
            + overlayValue("sliceThickness") + " mm"
            + "\nWL: " + overlayValue("windowCenter")
            + "   WW: " + overlayValue("windowWidth")
    }

    OverlayText {
        id: bottomRightText
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: viewportOverlay.overlayMargin
        width: Math.min(implicitWidth, viewportOverlay.width * 0.46)
        horizontalAlignment: Text.AlignRight
        text: "X: " + cursorValue("x")
            + "   Y: " + cursorValue("y")
            + "\nCT: " + cursorValue("value")
            + cursorValue("unit")
    }
}