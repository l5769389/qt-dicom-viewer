pragma ComponentBehavior: Bound
import QtQuick
import "../../../theme"

Item {
    id: root
    objectName: "viewportMetadataOverlay"
    required property var viewportController
    property bool hideSensitiveInfo: false
    property bool multiViewport: false
    readonly property var overlay: viewportController ? viewportController.overlayInfo : ({})
    readonly property var cursorInfo: viewportController ? viewportController.cursorController.cursorInfo : ({})
    readonly property var options: viewportController?.settingsController.values.corners ?? ({})
    readonly property bool petWorkspace: !!overlay.viewRole
    readonly property real bottomTextHeight: Math.max(bottomLeft.visible ? bottomLeft.height : 0,
                                                     bottomRight.visible ? bottomRight.height : 0)
    readonly property real topLeftTextHeight: topLeft.visible ? topLeft.height : 0
    readonly property real bottomLeftTextHeight: bottomLeft.visible ? bottomLeft.height : 0
    readonly property real fontScale: multiViewport || width < 640 || height < 480 ? 0.85 : 1
    readonly property color backgroundColor: viewportController?.canvasBackgroundColor ?? "#000000"
    readonly property bool lightBackground: backgroundColor.r * 0.299 + backgroundColor.g * 0.587 + backgroundColor.b * 0.114 > 0.6
    readonly property color textColor: options.colorMode === "custom" ? options.color : lightBackground ? "#182334" : Theme.overlayText
    visible: options.enabled !== false

    function value(key) {
        const text = String(overlay[key] ?? "").trim()
        return petWorkspace && (text === "--" || text === "—") ? "" : text
    }
    function label(key, title, unit = "") { const text = value(key); return text ? title + text + unit : "" }
    function planePosition() {
        return value("viewPosition")
            .replace(/^(Axial|Coronal|Sagittal|Oblique)/, name => name.toUpperCase())
            .replace(", ", " · ").replace(/(\d)mm\b/g, "$1 mm")
    }
    function field(key) {
        switch (key) {
        case "viewPosition": {
            const role = value("viewRole")
            if (role === "fusion")
                return ["FUSION", planePosition()].filter(Boolean).join(" · ")
            if (role === "mip") return value("viewType")
            if (role) return [role === "ct" ? "CT" : "PET", planePosition()].filter(Boolean).join(" · ")
            return value("viewPosition") || value("viewType").toUpperCase()
        }
        case "slice": {
            if (value("viewRole") === "mip") return overlay.registrationPreview ? "Reduced-resolution projection" : "Whole-volume projection"
            if (petWorkspace) return value("sliceIndex") ? "Reformatted slice: " + value("sliceIndex") + " / " + value("sliceCount")
                + (overlay.compactOverlay || !value("sourceSliceCount") ? "" : "\nSource images: " + value("sourceSliceCount")
                    + " (" + (value("viewRole") === "ct" ? "CT" : "PET") + ")") : ""
            return label("sliceIndex", "Slice: ") + (value("sliceCount") ? " / " + value("sliceCount") : "")
        }
        case "patientName": return hideSensitiveInfo ? "" : label("patientName", "Patient: ")
        case "patientId": return hideSensitiveInfo || overlay.suppressIdentifiers ? "" : label("patientId", "ID: ")
        case "seriesDescription": return value("viewRole") === "fusion"
            ? (hideSensitiveInfo ? "" : [label("ctSeries", "CT series: "), label("petSeries", "PET series: ")].filter(Boolean).join("\n"))
            : value(key)
        case "exposure": return value("modality") === "PT"
            ? [label("radiopharmaceutical", "Tracer: "),
               petWorkspace ? [label("correctedImage", "Corrections: "), label("decayCorrection", "Decay correction: ")].filter(Boolean).join("\n")
                   : "Correction: " + value("correctedImage") + " · " + value("decayCorrection")].filter(Boolean).join("\n")
            : [label("kvp", "kV: "), label("tubeCurrentMa", "mA: ")].filter(Boolean).join("   ")
        case "sliceThickness": return label("sliceThickness", petWorkspace ? "Source thickness: " : "Thickness: ", " mm")
        case "window": {
            if (value("modality") === "PT") {
                const lines = [label("petDisplayUpper", petWorkspace ? "Display range: 0 – " : "PET Range: 0 – ", " " + value("pixelUnit"))]
                if (!overlay.compactOverlay)
                    lines.push(label("petUnits", petWorkspace ? "DICOM units: " : "Source Units: "),
                               label("suvType", petWorkspace ? "SUV type: " : "SUV Type: "))
                if (value("viewRole") === "fusion")
                    lines.push([label("ctWindowCenter", "CT WL: "), label("ctWindowWidth", "WW: ")].filter(Boolean).join("  "))
                return lines.filter(Boolean).join("\n")
            }
            return [label("windowCenter", "WL: "), label("windowWidth", "WW: ")].filter(Boolean).join("   ")
        }
        case "cursor": if (overlay.registrationPreview) return "Preview MIP · Release to refine"
            return (petWorkspace ? "Col: " : "X: ") + (cursorInfo.x ?? "--") + (petWorkspace ? "   Row: " : "   Y: ") + (cursorInfo.y ?? "--")
            + "\n" + (value("viewRole") === "mip" ? "PET max" : cursorInfo.label ?? "Value") + ": " + (cursorInfo.value ?? "--") + " " + (cursorInfo.unit ?? "")
            + (viewportController?.secondaryCursorText ? "\n" + viewportController.secondaryCursorText : "")
        case "zoom": return label("zoom", "Zoom: ")
        case "matrix": return value("rows") && value("columns") ? (petWorkspace ? "Matrix: " : "") + value("rows") + " × " + value("columns") : ""
        case "spacing": return value("pixelSpacingX") && value("pixelSpacingY") ? (petWorkspace
            ? "Pixel spacing: " + value("pixelSpacingY") + " × " + value("pixelSpacingX")
            : value("pixelSpacingX") + " × " + value("pixelSpacingY")) + " mm" : ""
        default: return value(key)
        }
    }
    function lines(corner) {
        const compactFields = ["viewPosition", "slice", "patientName", "patientId", "window", "transform", "cursor"]
        return (options[corner] ?? []).filter(key => !overlay.compactOverlay || compactFields.includes(key))
            .map(key => field(key)).filter(Boolean).join("\n")
    }
    component CornerText: Item {
        id: corner
        property string text: ""
        property int horizontalAlignment: Text.AlignLeft
        readonly property real pixelSize: Math.max(10, Math.round((root.options.fontSize ?? 12) * root.fontScale))
        readonly property real rowHeight: pixelSize * (root.options.lineHeight ?? 1.2)
        readonly property int rowLimit: Math.max(0, Math.min(root.overlay.compactOverlay ? 4 : 12,
            Math.floor((root.height / 2 - 12) / rowHeight)))
        readonly property var rows: text.split("\n").filter(Boolean).slice(0, rowLimit)
        width: Math.max(0, (root.width - 24) / 2)
        height: rows.length * rowHeight
        clip: true
        visible: root.viewportController !== null && text.length > 0
        Column {
            width: parent.width
            Repeater {
                model: corner.rows.length
                Text {
                    required property int index
                    objectName: "cornerInformationLine"
                    width: corner.width
                    height: corner.rowHeight
                    text: corner.rows[index] ?? ""
                    color: root.textColor
                    font.pixelSize: corner.pixelSize
                    font.weight: root.overlay.compactOverlay ? Font.Normal : Font.DemiBold
                    horizontalAlignment: corner.horizontalAlignment
                    verticalAlignment: Text.AlignVCenter
                    style: Text.Outline
                    styleColor: root.lightBackground ? "#99ffffff" : Theme.overlayOutline
                    textFormat: Text.PlainText
                    wrapMode: Text.NoWrap
                    maximumLineCount: 1
                    elide: Text.ElideRight
                }
            }
        }
    }
    CornerText { id: topLeft; objectName: "overlay-topLeft"; anchors.left: parent.left; anchors.top: parent.top; anchors.margins: 2; text: root.lines("topLeft") }
    CornerText { objectName: "overlay-topRight"; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 2; horizontalAlignment: Text.AlignRight; text: root.lines("topRight") }
    CornerText { id: bottomLeft; objectName: "overlay-bottomLeft"; anchors.left: parent.left; anchors.bottom: parent.bottom; anchors.margins: 2; text: root.lines("bottomLeft") }
    CornerText { id: bottomRight; objectName: "overlay-bottomRight"; anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 2; horizontalAlignment: Text.AlignRight; text: root.lines("bottomRight") }
}
