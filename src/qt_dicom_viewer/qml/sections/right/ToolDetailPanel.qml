pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "components" as Components
import "panels" as Panels
import "../../theme"

Rectangle {
    id: detailPanel

    required property string activePanel
    required property var viewportController
    required property var toolController
    readonly property Item loadedPanel: contentLoader.item as Item
    readonly property string activeToolLabel:
        detailPanel.toolController
            ? detailPanel.toolController.activeToolLabel
            : ""
    readonly property string activeToolIcon:
        detailPanel.toolController
            ? detailPanel.toolController.activeToolIcon
            : ""

    implicitHeight: loadedPanel
        ? loadedPanel.implicitHeight + 80
        : 64
    color: Theme.panelBackgroundSoft

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        Components.ToolPanelHeader {
            Layout.fillWidth: true
            iconName: detailPanel.activeToolIcon
            title: detailPanel.activeToolLabel
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: Theme.dividerColor
        }

        Loader {
            id: contentLoader

            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredHeight: detailPanel.loadedPanel
                ? detailPanel.loadedPanel.implicitHeight
                : 0

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
