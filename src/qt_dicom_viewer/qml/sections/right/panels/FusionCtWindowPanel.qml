pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts

WindowLevelToolPanel {
    id: panel
    objectName: "fusionCtWindowPanel"
    required property var controller
    centerObjectName: "fusionCtCenter"
    widthObjectName: "fusionCtWidth"
    settingsController: controller?.toolController?.settingsController ?? null
    presets: (settingsController?.windowTemplates ?? []).filter(p => p.enabled)
    currentCenter: controller?.ctCenter ?? NaN
    currentWidth: controller?.ctWidth ?? NaN
    supportsInversion: true
    inverted: controller?.ctInverted ?? false
    onInversionRequested: controller?.toggleCtInverted()
    onActionTriggered: (presetId, center, width) => controller.setCtWindow(center, width)
}
