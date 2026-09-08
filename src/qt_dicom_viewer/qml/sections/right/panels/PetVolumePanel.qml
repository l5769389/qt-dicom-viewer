pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../../components" as Components
import "../../../theme"

ColumnLayout {
    id: panel
    objectName: "petVolumePanel"
    required property var controller
    readonly property var display: controller?.isFusionVolume === true ? controller : ({
        sceneLabel: "", volumeMode: "fusion", ctPreset: "bone", ctOpacity: 0,
        petUpper: 1, petThreshold: 0, petUnit: "", petOpacity: 0,
        colorMapOptions: [], petPalette: "hotIron"
    })
    spacing: 12
    Text { text: "三维显示"; color: Theme.textPrimary; font.pixelSize: 14; font.bold: true }
    Text {
        Layout.fillWidth: true
        text: "观察热点与解剖结构的空间关系。拖动旋转，滚轮缩放；配准和定量定位在融合四宫格完成。"
        color: Theme.textMuted; font.pixelSize: 12; wrapMode: Text.Wrap
    }
    ColumnLayout {
        Layout.fillWidth: true
        visible: panel.display.volumeMode !== "pet"
        Text { text: "CT 解剖结构"; color: Theme.textPrimary; font.bold: true }
        Components.AppComboBox {
            objectName: "fusionVolumeCtPreset"
            Layout.fillWidth: true
            model: [{label:"骨骼", value:"bone"}, {label:"通用组织", value:"general"}, {label:"肺", value:"lung"}]
            textRole: "label"
            currentIndex: model.findIndex(x => x.value === panel.display.ctPreset)
            onActivated: panel.controller.setCtPreset(model[currentIndex].value)
        }
        Text { text: "CT 不透明度  " + Math.round(panel.display.ctOpacity * 100) + "%"; color: Theme.textMuted }
        Components.AppSlider {
            objectName: "fusionVolumeCtOpacity"
            Layout.fillWidth: true
            from: 0; to: 1; value: panel.display.ctOpacity
            onMoved: panel.controller.setCtOpacity(value)
        }
    }
    ColumnLayout {
        Layout.fillWidth: true
        visible: panel.display.volumeMode !== "ct"
        Text { text: "PET 热点"; color: Theme.textPrimary; font.bold: true }
        Text {
            Layout.fillWidth: true
            text: "显示范围 0 – " + Number(panel.display.petUpper.toPrecision(4)) + " " + panel.display.petUnit
            color: Theme.textMuted; wrapMode: Text.Wrap
        }
        RowLayout {
            Layout.fillWidth: true
            Text { text: "隐藏低于"; color: Theme.textMuted }
            Components.AppNumberField {
                objectName: "fusionVolumePetThreshold"
                Layout.fillWidth: true
                numberValue: panel.display.petThreshold
                minimum: 0; maximum: panel.display.petUpper * .99; decimals: 3
                onEdited: value => panel.controller.setPetThreshold(value)
            }
            Text { text: panel.display.petUnit; color: Theme.textMuted; font.pixelSize: 11 }
        }
        Text { text: "PET 不透明度  " + Math.round(panel.display.petOpacity * 100) + "%"; color: Theme.textMuted }
        Components.AppSlider {
            objectName: "fusionVolumePetOpacity"
            Layout.fillWidth: true
            from: 0; to: 1; value: panel.display.petOpacity
            onMoved: panel.controller.setPetOpacity(value)
        }
        Components.AppComboBox {
            objectName: "fusionVolumePetPalette"
            Layout.fillWidth: true
            model: panel.display.colorMapOptions
            textRole: "label"
            currentIndex: model.findIndex(x => x.colorMap === panel.display.petPalette)
            onActivated: panel.controller.setPetPalette(model[currentIndex].colorMap)
        }
    }
}
