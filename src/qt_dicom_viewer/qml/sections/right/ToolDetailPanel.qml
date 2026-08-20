pragma
ComponentBehavior: Bound

import QtQuick
import "panels" as Panels

Rectangle {
    id: detailPanel

    required property var activePanel
    required property var activeViewport
    required property var toolController

    color: "#171b21"

    Loader {
        anchors.fill: parent
        anchors.margins: 12


        active: detailPanel.activePanel !== ""
        sourceComponent: {
            switch (detailPanel.activePanel) {
                case 'rotate':
                    return rotatePanelComponent
                case 'window':
                    return windowLevelComponent
                default:
                    return null
            }
        }
    }

    Component {
        id: rotatePanelComponent
        Panels.RotateToolPanel {
            toolController:detailPanel.toolController
            onActionTriggered: action => {
                activeViewport?.applyTransformAction(action)
            }
        }
    }

    Component {
        id: windowLevelComponent
        Panels.WindowLevelToolPanel {
            presets: toolController.windowPresets

            onActionTriggered: (presetId, center, width) => {
                activeViewport?.windowPresetRequested(
                    presetId,
                    center,
                    width
                )
            }
        }
    }

}