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
    property var exportController: null
    property Item exportItem: null
    signal manualRequested(string chapter)
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
            Layout.minimumWidth: 0
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
                if (detailPanel.activePanel === "pseudocolor")
                    return detailPanel.viewportController?.reconstructionController
                        ? petColorComponent : pseudoColorComponent
                const map = {
                    'scroll': scrollComponent,
                    'zoom': zoomComponent,
                    'export': exportComponent,
                    'segmentation': voiComponent,
                    'voi': voiComponent,
                    'ct-window': ctWindowComponent,
                    'pet-window': petWorkspaceComponent,
                    'registration': petRegistrationComponent,
                    'fusion-blend': fusionBlendComponent,
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
        id: scrollComponent
        Panels.ScrollToolPanel { viewportController: detailPanel.viewportController }
    }
    Component {
        id: zoomComponent
        Panels.ZoomToolPanel { viewportController: detailPanel.viewportController }
    }

    Component {
        id: exportComponent
        Panels.ExportPanel { exportController: detailPanel.exportController; exportItem: detailPanel.exportItem }
    }

    Component {
        id: voiComponent
        Panels.MprVoiPanel {
            controller: detailPanel.tabController?.voiController ?? detailPanel.viewportController?.voiController ?? null
            mode: detailPanel.activePanel
            onManualRequested: chapter => detailPanel.manualRequested(chapter)
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
        Loader {
            sourceComponent: detailPanel.viewportController?.isStandalonePetVolume === true
                ? standalonePetVolumeComponent : detailPanel.viewportController?.isFusionVolume === true
                ? petVolumeComponent : genericVolumePresetComponent
        }
    }
    Component {
        id: genericVolumePresetComponent
        Panels.VolumePresetPanel { viewportController: detailPanel.viewportController }
    }
    Component {
        id: standalonePetVolumeComponent
        Panels.StandalonePetVolumePanel { controller: detailPanel.viewportController }
    }
    Component {
        id: petVolumeComponent
        Panels.PetVolumePanel { controller: detailPanel.viewportController }
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
        id: petColorComponent
        Panels.PetColorPanel {
            controller: detailPanel.viewportController.reconstructionController
            Component.onCompleted: fusionTarget = detailPanel.viewportController.viewportRole === "fusion"
        }
    }

    Component {
        id: fusionBlendComponent
        Panels.FusionBlendPanel {
            controller: detailPanel.viewportController.reconstructionController
        }
    }

    Component {
        id: petRegistrationComponent
        Panels.PetRegistrationPanel {
            controller: detailPanel.viewportController.reconstructionController
        }
    }

    Component {
        id: ctWindowComponent
        Panels.FusionCtWindowPanel {
            controller: detailPanel.viewportController?.reconstructionController ?? null
        }
    }

    Component {
        id: petWorkspaceComponent
        Panels.PetWorkspacePanel {
            controller: detailPanel.viewportController?.reconstructionController ?? null
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
            settingsController: detailPanel.toolController?.settingsController ?? null
            currentCenter: detailPanel.viewportController?.windowCenter ?? NaN
            currentWidth: detailPanel.viewportController?.windowWidth ?? NaN
            allowEditing: detailPanel.viewportController?.isPetViewport !== true
            supportsInversion: detailPanel.viewportController?.supportsCtWindow === true
                && detailPanel.viewportController?.viewportType !== "volume"
            inverted: detailPanel.viewportController?.inverted ?? false
            onInversionRequested: detailPanel.viewportController?.toggleInverted()
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
            onManualRequested: detailPanel.manualRequested("measurement")
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
            onManualRequested: chapter => detailPanel.manualRequested(chapter)
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
