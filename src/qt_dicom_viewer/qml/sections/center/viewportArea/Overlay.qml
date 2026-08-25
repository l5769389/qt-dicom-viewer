import QtQuick
import QtQuick.Layouts
import "../../../theme"

pragma ComponentBehavior: Bound

Item {
    id: viewportOverlay

    required property var viewportController

    readonly property int overlayMargin: 2
    readonly property var overlay:
        viewportController ? viewportController.overlayInfo : ({})
    readonly property var cursorInfo:
        viewportController
            ? viewportController.cursorController.cursorInfo
            : ({})

    component OverlayText: Text {
        visible: viewportOverlay.viewportController !== null
            && text.length > 0
        color: Theme.overlayText
        font.pixelSize: 12
        font.weight: Font.DemiBold
        font.letterSpacing: 0.15
        lineHeight: 1.28
        style: Text.Outline
        styleColor: Theme.overlayOutline
        wrapMode: Text.Wrap
        z: 2
    }

    function displayValue(value, showPlaceholder) {
        if (value === undefined || value === null)
            return showPlaceholder ? "--" : ""

        const text = String(value).trim()
        if (text.length === 0)
            return showPlaceholder ? "--" : ""

        return text
    }

    function overlayValue(key, showPlaceholder = false) {
        return displayValue(overlay[key], showPlaceholder)
    }

    function cursorValue(key, showPlaceholder = false) {
        return displayValue(cursorInfo[key], showPlaceholder)
    }

    function labeledPair(
        leftLabel,
        leftValue,
        rightLabel,
        rightValue
    ) {
        const values = []

        if (leftValue !== "")
            values.push(leftLabel + ": " + leftValue)

        if (rightValue !== "")
            values.push(rightLabel + ": " + rightValue)

        return values.join("   ")
    }

    OverlayText {
        id: topLeftText

        anchors.left: parent.left
        anchors.top: parent.top
        anchors.margins: viewportOverlay.overlayMargin
        width: Math.min(implicitWidth, viewportOverlay.width * 0.46)

        text: {
            const lines = []
            const manufacturer = overlayValue("manufacturer")
            const seriesDescription = overlayValue("seriesDescription")
            const viewType = overlayValue("viewType")
            const sliceLocation = overlayValue("sliceLocation")
            const sliceIndex = overlayValue("sliceIndex")
            const sliceCount = overlayValue("sliceCount")

            if (manufacturer !== "")
                lines.push(manufacturer)

            if (seriesDescription !== "")
                lines.push(seriesDescription)

            if (viewType !== "")
                lines.push(viewType.toUpperCase())

            if (sliceLocation !== "")
                lines.push("Location: " + sliceLocation)

            if (sliceIndex !== "" && sliceCount !== "") {
                lines.push("Slice: " + sliceIndex + " / " + sliceCount)
            } else if (sliceIndex !== "") {
                lines.push("Slice: " + sliceIndex)
            }

            return lines.join("\n")
        }
    }

    OverlayText {
        id: topRightText

        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: viewportOverlay.overlayMargin
        width: Math.min(implicitWidth, viewportOverlay.width * 0.46)
        horizontalAlignment: Text.AlignRight

        text: {
            const lines = []
            const patientName = overlayValue("patientName")
            const patientId = overlayValue("patientId")

            if (patientName !== "")
                lines.push("Patient: " + patientName)

            if (patientId !== "")
                lines.push("ID: " + patientId)

            return lines.join("\n")
        }
    }

    OverlayText {
        id: bottomLeftText

        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: viewportOverlay.overlayMargin
        width: Math.min(implicitWidth, viewportOverlay.width * 0.46)

        text: {
            const lines = []
            const exposure = labeledPair(
                "kV",
                overlayValue("kvp"),
                "mA",
                overlayValue("tubeCurrentMa")
            )
            const sliceThickness = overlayValue("sliceThickness")
            const window = labeledPair(
                "WL",
                overlayValue("windowCenter"),
                "WW",
                overlayValue("windowWidth")
            )

            if (exposure !== "")
                lines.push(exposure)

            if (sliceThickness !== "")
                lines.push("Thickness: " + sliceThickness + " mm")

            if (window !== "")
                lines.push(window)

            return lines.join("\n")
        }
    }

    OverlayText {
        id: bottomRightText

        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: viewportOverlay.overlayMargin
        width: Math.min(implicitWidth, viewportOverlay.width * 0.46)
        horizontalAlignment: Text.AlignRight

        text: "X: " + cursorValue("x", true)
            + "   Y: " + cursorValue("y", true)
            + "\nCT: " + cursorValue("value", true)
            + cursorValue("unit")
    }
}
