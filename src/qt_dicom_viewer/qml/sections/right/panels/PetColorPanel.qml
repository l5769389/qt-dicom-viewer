pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../../components" as Components
import "../../../theme"

ColumnLayout {
    id: panel
    objectName: "petColorPanel"
    required property var controller
    property bool fusionTarget: false
    property bool showAllPalettes: false
    readonly property var commonPalettes: ["grayscale-inverted", "grayscale", "hotIron", "hotMetal", "pet", "rainbow"]
    spacing: 12

    Text { text: "伪彩"; color: Theme.textPrimary; font.pixelSize: 14; font.bold: true }
    RowLayout {
        Layout.fillWidth: true
        Components.AppButton {
            objectName: "paletteTarget-pet"
            Layout.fillWidth: true
            text: panel.controller.isFusion ? "PET / MIP" : "PET"
            checkable: true
            checked: !panel.fusionTarget
            onClicked: panel.fusionTarget = false
        }
        Components.AppButton {
            objectName: "paletteTarget-fusion"
            visible: panel.controller.isFusion
            Layout.fillWidth: true
            text: "融合层"
            checkable: true
            checked: panel.fusionTarget
            onClicked: panel.fusionTarget = true
        }
    }
    PseudoColorPanel {
        Layout.fillWidth: true
        description: panel.fusionTarget
            ? "设置融合格内 PET 叠加层的色表。"
            : "设置 PET 与 MIP 的共用色表。"
        viewportController: QtObject {
            readonly property var colorMapOptions: panel.controller.petController.colorMapOptions.filter(
                entry => panel.showAllPalettes || panel.commonPalettes.includes(entry.colorMap)
                    || entry.colorMap === activeColorMap)
            readonly property string activeColorMap: panel.fusionTarget
                ? panel.controller.fusionColorMap : panel.controller.petColorMap
            function applyColorMap(value) {
                if (panel.fusionTarget) panel.controller.setFusionColorMap(value)
                else panel.controller.setPetColorMap(value)
            }
        }
    }
    Components.AppButton {
        objectName: "toggleMorePetColors"
        Layout.fillWidth: true
        compact: true
        text: panel.showAllPalettes ? "收起更多色表" : "更多色表"
        onClicked: panel.showAllPalettes = !panel.showAllPalettes
    }
}
