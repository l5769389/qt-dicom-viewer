pragma ComponentBehavior: Bound

import QtQuick
import "panels" as Panels
import "../../theme"

Rectangle {
    id: detailPanel

    required property string activePanel
    required property var viewportController
    required property var toolController

    color: Theme.panelBackgroundSoft

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
                if (detailPanel.viewportController) {
                    detailPanel.viewportController.applyTransformAction(action)
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
                if (detailPanel.viewportController) {
                    detailPanel.viewportController.applyWindowPreset(
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
            toolController: detailPanel.toolController
            onActionTriggered: action => {
                if (detailPanel.toolController) {
                    detailPanel.toolController.selectInteraction(action)
                }
            }
        }
    }

    Component {
        id: annotateComponent
        Panels.AnnotatePanel {

        }
    }

}
