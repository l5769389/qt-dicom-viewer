pragma ComponentBehavior: Bound
import QtQuick
import "../../../theme"

Item {
    id: root
    required property var viewportController
    readonly property var overlay: viewportController ? viewportController.overlayInfo : ({})
    readonly property var cursorInfo: viewportController ? viewportController.cursorController.cursorInfo : ({})
    readonly property var options: viewportController?.settingsController.values.corners ?? ({})
    readonly property color backgroundColor: viewportController?.canvasBackgroundColor ?? "#000000"
    readonly property bool lightBackground: backgroundColor.r * 0.299 + backgroundColor.g * 0.587 + backgroundColor.b * 0.114 > 0.6
    readonly property color textColor: options.colorMode === "custom" ? options.color : lightBackground ? "#182334" : Theme.overlayText
    visible: options.enabled !== false

    function value(key) { return String(overlay[key] ?? "").trim() }
    function label(key, title, unit = "") { const text = value(key); return text ? title + text + unit : "" }
    function field(key) {
        switch (key) {
        case "viewPosition": return value("viewPosition") || value("viewType").toUpperCase()
        case "slice": return label("sliceIndex", "Slice: ") + (value("sliceCount") ? " / " + value("sliceCount") : "")
        case "patientName": return label("patientName", "Patient: ")
        case "patientId": return label("patientId", "ID: ")
        case "exposure": return [label("kvp", "kV: "), label("tubeCurrentMa", "mA: ")].filter(Boolean).join("   ")
        case "sliceThickness": return label("sliceThickness", "Thickness: ", " mm")
        case "window": return [label("windowCenter", "WL: "), label("windowWidth", "WW: ")].filter(Boolean).join("   ")
        case "cursor": return "X: " + (cursorInfo.x ?? "--") + "   Y: " + (cursorInfo.y ?? "--")
            + "\n" + (value("modality") === "CT" ? "CT: " : "Value: ") + (cursorInfo.value ?? "--") + (cursorInfo.unit ?? "")
        case "zoom": return label("zoom", "Zoom: ")
        case "matrix": return [value("rows"), value("columns")].filter(Boolean).join(" × ")
        case "spacing": return value("pixelSpacingX") && value("pixelSpacingY") ? value("pixelSpacingX") + " × " + value("pixelSpacingY") + " mm" : ""
        default: return value(key)
        }
    }
    function lines(corner) { return (options[corner] ?? []).map(key => field(key)).filter(Boolean).join("\n") }
    component CornerText: Text {
        color: root.textColor
        font.pixelSize: root.options.fontSize ?? 12
        font.weight: Font.DemiBold
        lineHeight: root.options.lineHeight ?? 1.2
        style: Text.Outline
        styleColor: root.lightBackground ? "#99ffffff" : Theme.overlayOutline
        textFormat: Text.PlainText
        wrapMode: Text.Wrap
        width: Math.min(implicitWidth, root.width * 0.46)
        maximumLineCount: 12
        elide: Text.ElideRight
        visible: root.viewportController !== null && text.length > 0
    }
    CornerText { objectName: "overlay-topLeft"; anchors.left: parent.left; anchors.top: parent.top; anchors.margins: 2; text: root.lines("topLeft") }
    CornerText { objectName: "overlay-topRight"; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 2; horizontalAlignment: Text.AlignRight; text: root.lines("topRight") }
    CornerText { objectName: "overlay-bottomLeft"; anchors.left: parent.left; anchors.bottom: parent.bottom; anchors.margins: 2; text: root.lines("bottomLeft") }
    CornerText { objectName: "overlay-bottomRight"; anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 2; horizontalAlignment: Text.AlignRight; text: root.lines("bottomRight") }
}
