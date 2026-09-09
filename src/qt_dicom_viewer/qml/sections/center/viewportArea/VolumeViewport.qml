pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../../components" as Components
import "../../../theme"

Item {
    id: root
    objectName: "volumeViewport"
    required property var viewportController
    property var attachedController: null

    function attach() {
        const next = viewportController && viewportController.viewportType === "volume"
            && viewportController.loadState === "ready" ? viewportController : null
        if (next !== attachedController) {
            if (attachedController)
                attachedController.setNativeVisible(false)
            // Detach the old QWindow while its Python owner is still alive.
            attachedController = null
            if (next) {
                next.ensureNativeView()
                attachedController = next
            }
        }
        Qt.callLater(syncVisibility)
    }

    function syncVisibility() {
        if (attachedController)
            attachedController.setNativeVisible(root.visible)
    }

    Connections {
        target: root.viewportController
        ignoreUnknownSignals: true
        function onLoadStateChanged() { root.attach() }
    }
    onViewportControllerChanged: attach()
    onVisibleChanged: syncVisibility()
    Component.onCompleted: attach()
    Component.onDestruction: {
        if (attachedController)
            attachedController.setNativeVisible(false)
        attachedController = null
    }

    RowLayout {
        id: fusionHeader
        visible: root.viewportController?.isFusionVolume === true
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: visible ? 38 : 0
        spacing: 6
        Text {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            text: fusionHeader.visible ? root.viewportController.sceneLabel : ""
            color: Theme.textPrimary; font.pixelSize: 12; elide: Text.ElideRight
        }
        Repeater {
            model: fusionHeader.visible ? [{label:"CT 3D",value:"ct"},{label:"PET 3D",value:"pet"},{label:"融合 3D",value:"fusion"}] : []
            delegate: Components.AppButton {
                required property var modelData
                objectName: "volumeMode-" + modelData.value
                text: modelData.label
                compact: true; checkable: true
                checked: root.viewportController.volumeMode === modelData.value
                onClicked: root.viewportController.setVolumeMode(modelData.value)
            }
        }
    }

    WindowContainer {
        objectName: "volumeWindowContainer"
        anchors.fill: parent
        anchors.margins: 2
        anchors.topMargin: fusionHeader.visible ? fusionHeader.height + 2 : 2
        window: root.attachedController ? root.attachedController.nativeWindow : null
    }
}
