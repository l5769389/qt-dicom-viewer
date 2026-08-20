pragma
ComponentBehavior: Bound

import QtQuick
import "panels" as Panels

Rectangle {
    id: detailPanel

    required property string activePanel
    required property var activeViewport
    required property var toolController

    color: "#171b21"

    Loader {
        anchors.fill: parent
        anchors.margins: 12


        active: detailPanel.activePanel !== ""
        sourceComponent: {
            const map = {
                'rotate': rotatePanelComponent,
                'window': windowLevelComponent,
                'measure': measureComponent,
                "annotate": annotateComponent
            }
            return map[detailPanel.activePanel] ?? null
        }
    }

    Component {
        id: rotatePanelComponent
        Panels.RotateToolPanel {
            toolController: detailPanel.toolController
            onActionTriggered: action => {
                if (detailPanel.activeViewport) {
                    detailPanel.activeViewport.applyTransformAction(action)
                }
            }
        }
    }

    Component {
        id: windowLevelComponent
        Panels.WindowLevelToolPanel {
            presets: detailPanel.toolController
                ? detailPanel.toolController.windowPresets
                : []

            onActionTriggered: (presetId, center, width) => {
                if (detailPanel.activeViewport) {
                    detailPanel.activeViewport.applyWindowPreset(
                        center,
                        width
                    )
                }
            }
        }
    }

    Component {
        id: measureComponent
        Panels.MeasurePanel {

        }
    }

    Component {
        id: annotateComponent
        Panels.AnnotatePanel {

        }
    }

}
