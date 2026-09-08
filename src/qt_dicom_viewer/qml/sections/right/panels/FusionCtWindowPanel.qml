pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../../components" as Components
import "../../../theme"

ColumnLayout {
    id: panel
    objectName: "fusionCtWindowPanel"
    required property var controller
    spacing: 12

    RowLayout {
        Layout.fillWidth: true
        spacing: 10
        ColumnLayout {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            spacing: 6
            Text { text: "窗位 · WL"; color: Theme.textMuted; font.pixelSize: 12 }
            Components.AppNumberField {
                objectName: "fusionCtCenter"
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignRight
                font.pixelSize: Theme.bodyFontSize
                numberValue: panel.controller?.ctCenter ?? 40
                minimum: -1e12; maximum: 1e12; decimals: 1
                onEdited: value => panel.controller.setCtWindow(value, panel.controller.ctWidth)
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            spacing: 6
            Text { text: "窗宽 · WW"; color: Theme.textMuted; font.pixelSize: 12 }
            Components.AppNumberField {
                objectName: "fusionCtWidth"
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignRight
                font.pixelSize: Theme.bodyFontSize
                numberValue: panel.controller?.ctWidth ?? 400
                minimum: 1; maximum: 1e12; decimals: 1
                onEdited: value => panel.controller.setCtWindow(panel.controller.ctCenter, value)
            }
        }
    }

    WindowLevelToolPanel {
        Layout.fillWidth: true
        // Share built-in, custom and enabled presets with the 2D viewer.
        presets: (panel.controller?.toolController?.settingsController?.windowTemplates ?? []).filter(p => p.enabled)
        currentCenter: panel.controller?.ctCenter ?? NaN
        currentWidth: panel.controller?.ctWidth ?? NaN
        onActionTriggered: (presetId, center, width) => panel.controller.setCtWindow(center, width)
    }
}
