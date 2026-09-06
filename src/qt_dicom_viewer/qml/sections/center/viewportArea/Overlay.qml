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
        wrapMode: overlayValue("viewRole") === "fusion" ? Text.NoWrap : Text.Wrap
        elide: overlayValue("viewRole") === "fusion" ? Text.ElideRight : Text.ElideNone

        anchors.left: parent.left
        anchors.top: parent.top
        anchors.margins: viewportOverlay.overlayMargin
        width: Math.min(implicitWidth, viewportOverlay.width * 0.46)

        text: {
            const lines = []
            const modality = overlayValue("modality")
            const role = overlayValue("viewRole")
            if (role === "fusion") {
                lines.push("PET/CT FUSION · " + overlayValue("viewType").toUpperCase())
                lines.push("CT: " + overlayValue("ctSeries"))
                lines.push("PET: " + overlayValue("petSeries"))
                lines.push("Image: " + overlayValue("sliceIndex") + " / " + overlayValue("sliceCount"))
                return lines.join("\n")
            } else if (role === "ct" || role === "pet") {
                lines.push(role.toUpperCase() + " · " + overlayValue("viewType").toUpperCase())
            } else if (role === "mip") {
                lines.push("PET MIP · 最大值投影")
            } else if (role !== "") {
                lines.push("PET " + overlayValue("viewType").toUpperCase())
            }
            const manufacturer = overlayValue("manufacturer")
            const seriesDescription = overlayValue("seriesDescription")
            const studyDescription = overlayValue("studyDescription")
            const viewType = overlayValue("viewType")
            const sliceLocation = overlayValue("sliceLocation")
            const sliceIndex = overlayValue("sliceIndex")
            const sliceCount = overlayValue("sliceCount")

            if (manufacturer !== "")
                lines.push(manufacturer)

            if (modality === "PT") {
                if (studyDescription !== "")
                    lines.push("PET · " + studyDescription)
                if (seriesDescription !== "")
                    lines.push(seriesDescription)
                if (role !== "mip" && sliceIndex !== "" && sliceCount !== "")
                    lines.push("Image: " + sliceIndex + " / " + sliceCount)
                return lines.join("\n")
            }

            if (seriesDescription !== "") lines.push(seriesDescription)

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
            const modality = overlayValue("modality")
            const patientName = overlayValue("patientName")
            const patientId = overlayValue("patientId")

            if (patientName !== "")
                lines.push("Patient: " + patientName)

            if (patientId !== "")
                lines.push("ID: " + patientId)

            if (modality === "PT") {
                const tracer = overlayValue("radiopharmaceutical")
                const corrections = overlayValue("correctedImage")
                const decay = overlayValue("decayCorrection")
                if (tracer !== "")
                    lines.push("Tracer: " + tracer)
                if (corrections !== "" || decay !== "")
                    lines.push("Correction: " + corrections
                        + (corrections !== "" && decay !== "" ? " · " : "")
                        + decay)
            }

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
            const modality = overlayValue("modality")

            if (modality === "PT") {
                const sourceUnit = overlayValue("petUnits")
                const pixelUnit = overlayValue("pixelUnit")
                const suvType = overlayValue("suvType")
                const lower = overlayValue("petDisplayLower", true)
                const upper = overlayValue("petDisplayUpper", true)
                lines.push("PET Range: " + lower + " – " + upper
                    + (pixelUnit === "" ? "" : " " + pixelUnit))
                if (sourceUnit !== "")
                    lines.push("Source Units: " + sourceUnit)
                if (suvType !== "")
                    lines.push("SUV Type: " + suvType)
                if (sliceThickness !== "")
                    lines.push("Slice Thickness: " + sliceThickness + " mm")
                if (overlayValue("viewRole") === "fusion") {
                    lines.push("CT WL: " + overlayValue("ctWindowCenter")
                        + "  WW: " + overlayValue("ctWindowWidth"))
                    lines.push(overlayValue("registration"))
                }
                return lines.join("\n")
            }

            if (exposure !== "") lines.push(exposure)
            if (sliceThickness !== "") lines.push("Thickness: " + sliceThickness + " mm")
            if (window !== "") lines.push(window)

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

        text: {
            const sample = "X: " + cursorValue("x", true)
                + "   Y: " + cursorValue("y", true)
                + "\n" + cursorValue("label", true) + ": "
                + cursorValue("value", true)
                + (cursorValue("unit") === ""
                    ? "" : " " + cursorValue("unit"))
            if (overlayValue("modality") !== "PT")
                return sample
            const secondary = viewportController.secondaryCursorText ?? ""
            return "Zoom: " + overlayValue("zoom", true)
                + "   Rot: " + overlayValue("rotation", true) + "°"
                + "   Flip: " + overlayValue("flip", true)
                + "\n" + sample.replace("\n", "   ")
                + (secondary === "" ? "" : "\n" + secondary)
        }
    }
}
