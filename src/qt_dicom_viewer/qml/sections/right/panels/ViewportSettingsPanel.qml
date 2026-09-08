pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../../theme"
import "../../../components" as Components

ColumnLayout {
    id: settingsPanel
    objectName: "viewportSettingsPanel"
    required property var viewportController
    spacing: 4
    readonly property var petWorkspace: viewportController?.reconstructionController ?? null

    ColumnLayout {
        Layout.fillWidth: true
        visible: settingsPanel.petWorkspace !== null
        spacing: 8
        Text { text: "PET 工作区"; color: Theme.textPrimary; font.bold: true }
        Text { text: "定位标记样式"; color: Theme.textMuted; font.pixelSize: 12 }
        RowLayout {
            Layout.fillWidth: true
            Repeater {
                model: [{label:"小十字", compact:true}, {label:"参考线", compact:false}]
                delegate: Components.AppButton {
                    required property var modelData
                    objectName: "petLocator-" + (modelData.compact ? "compact" : "lines")
                    Layout.fillWidth: true
                    text: modelData.label
                    compact: true; checkable: true; autoExclusive: true; baseBorderWidth: 1
                    checked: settingsPanel.petWorkspace?.compactCrosshair === modelData.compact
                    onClicked: settingsPanel.petWorkspace.setCompactCrosshair(modelData.compact)
                }
            }
        }
        Text { text: "四角信息"; color: Theme.textMuted; font.pixelSize: 12 }
        RowLayout {
            Layout.fillWidth: true
            Repeater {
                model: [{label:"精简", compact:true}, {label:"详细", compact:false}]
                delegate: Components.AppButton {
                    required property var modelData
                    objectName: "petInfo-" + (modelData.compact ? "compact" : "detail")
                    Layout.fillWidth: true
                    text: modelData.label
                    compact: true; checkable: true; autoExclusive: true; baseBorderWidth: 1
                    checked: settingsPanel.petWorkspace?.compactOverlay === modelData.compact
                    onClicked: settingsPanel.petWorkspace.setCompactOverlay(modelData.compact)
                }
            }
        }
        Text { text: "应用于当前 PET 工作区的四格"; color: Theme.textMuted; font.pixelSize: 11 }
        Rectangle { Layout.fillWidth: true; height: 1; color: Theme.dividerColor }
    }

    readonly property var settings: [
        {code: "window-annotations", label: "窗口标注信息", separator: false},
        {code: "hide-sensitive-info", label: "隐藏患者敏感信息", separator: false},
        {code: "scale-bar", label: "比例尺", separator: false},
        {code: "color-bar", label: "伪彩条", separator: false},
        {code: "dicom-overlay", label: "DICOM Overlay", separator: false},
        {code: "localizer", label: "定位线", separator: true},
        {code: "fit-to-window", label: "窗口大小自适应", separator: true}
    ]

    function valueFor(code) {
        const controller = settingsPanel.viewportController
        if (!controller)
            return false
        switch (code) {
        case "window-annotations": return controller.showWindowAnnotations
        case "hide-sensitive-info": return controller.hideSensitiveInfo
        case "scale-bar": return controller.showScaleBar
        case "color-bar": return controller.showColorBar
        case "dicom-overlay": return controller.showDicomOverlay
        case "localizer": return controller.showLocalizer
        case "fit-to-window": return controller.fitToWindow
        default: return false
        }
    }

    Repeater {
        model: settingsPanel.settings

        delegate: ColumnLayout {
            id: settingRow
            required property var modelData
            Layout.fillWidth: true
            spacing: 4

            Rectangle {
                visible: settingRow.modelData.separator
                Layout.fillWidth: true
                Layout.topMargin: 3
                height: 1
                color: Theme.dividerColor
            }

            Components.AppCheckBox {
                id: settingCheckBox
                objectName: "viewportSetting-" + settingRow.modelData.code
                Layout.fillWidth: true
                implicitHeight: 36
                text: settingRow.modelData.label
                checked: settingsPanel.valueFor(settingRow.modelData.code)
                onToggled: settingsPanel.viewportController?.setViewportSetting(
                    settingRow.modelData.code,
                    checked
                )



            }
        }
    }

    Item { Layout.fillHeight: true }
}
