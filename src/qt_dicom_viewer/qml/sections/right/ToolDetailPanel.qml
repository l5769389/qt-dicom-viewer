pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "panels" as Panels
import "../../theme"

Rectangle {
    id: detailPanel

    required property string activePanel
    required property var viewportController
    required property var toolController
    property var tabController: null
    readonly property Item loadedPanel: contentLoader.item as Item
    readonly property string activeToolLabel:
        detailPanel.toolController
            ? detailPanel.toolController.activeToolLabel
            : ""
    readonly property string activeToolIcon:
        detailPanel.toolController
            ? detailPanel.toolController.activeToolIcon
            : ""
    readonly property bool petIntensityMode:
        detailPanel.viewportController
            ? detailPanel.viewportController.isPetViewport === true
            : false

    implicitHeight: loadedPanel
        ? loadedPanel.implicitHeight + 24
        : 64
    color: Theme.panelBackgroundSoft

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        Loader {
            id: contentLoader

            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            Layout.preferredHeight: detailPanel.loadedPanel
                ? detailPanel.loadedPanel.implicitHeight
                : 0

            active: detailPanel.activePanel !== ""
            sourceComponent: {
                if (detailPanel.activePanel === "window")
                    return detailPanel.viewportController
                        && detailPanel.viewportController.reconstructionController
                        ? petWorkspaceComponent : detailPanel.petIntensityMode
                        ? petIntensityComponent : windowLevelComponent
                const map = {
                    'rotate': rotatePanelComponent,
                    'mip': mipPanelComponent,
                    'measure': measureComponent,
                    "annotate": annotateComponent,
                    "pseudocolor": pseudoColorComponent,
                    "viewport-settings": viewportSettingsComponent,
                    "service": serviceComponent,
                    "volume-direction": volumeDirectionComponent,
                    "volume-preset": volumePresetComponent,
                    "volume-crop": volumeCropComponent,
                    "play": playbackComponent
                }
                return map[detailPanel.activePanel] ?? null
            }
        }
    }

    Component {
        id: volumeCropComponent
        Panels.VolumeCropPanel {
            viewportController: detailPanel.viewportController
        }
    }

    Component {
        id: volumeDirectionComponent
        Panels.VolumeDirectionPanel {
            viewportController: detailPanel.viewportController
        }
    }

    Component {
        id: volumePresetComponent
        Panels.VolumePresetPanel {
            viewportController: detailPanel.viewportController
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
        id: mipPanelComponent
        Panels.MipPanel {
            toolController: detailPanel.toolController
        }
    }

    Component {
        id: petWorkspaceComponent
        Panels.PetWorkspacePanel {
            controller: detailPanel.viewportController.reconstructionController
        }
    }

    Component {
        id: petIntensityComponent
        Panels.PetIntensityPanel {
            viewportController: detailPanel.viewportController
        }
    }

    Component {
        id: windowLevelComponent
        Panels.WindowLevelToolPanel {
            presets: detailPanel.viewportController
                && detailPanel.viewportController.windowPresets !== undefined
                ? detailPanel.viewportController.windowPresets
                : detailPanel.toolController
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
        id: serviceComponent
        Panels.ServicePanel {
            toolController: detailPanel.toolController
            viewportController: detailPanel.viewportController
            onActionTriggered: action => {
                detailPanel.toolController?.selectService(action)
            }
        }
    }

    Component {
        id: annotateComponent
        Panels.AnnotatePanel {
            viewportController: detailPanel.viewportController
        }
    }

    Component {
        id: pseudoColorComponent
        Panels.PseudoColorPanel {
            viewportController: detailPanel.viewportController
        }
    }

    Component {
        id: viewportSettingsComponent
        Panels.ViewportSettingsPanel {
            viewportController: detailPanel.viewportController
        }
    }

    Component {
        id: playbackComponent
        Panels.PlaybackPanel {
            tabController: detailPanel.tabController
        }
    }

}
