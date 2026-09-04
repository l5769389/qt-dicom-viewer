pragma ComponentBehavior: Bound
import QtQuick

Item {
    id: root
    objectName: "volumeViewport"
    required property var viewportController
    property var attachedController: null

    function attach() {
        const next = viewportController && viewportController.viewportType === "volume"
            ? viewportController : null
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

    onViewportControllerChanged: attach()
    onVisibleChanged: syncVisibility()
    Component.onCompleted: attach()
    Component.onDestruction: {
        if (attachedController)
            attachedController.setNativeVisible(false)
        attachedController = null
    }

    WindowContainer {
        objectName: "volumeWindowContainer"
        anchors.fill: parent
        anchors.margins: 2
        window: root.attachedController ? root.attachedController.nativeWindow : null
    }
}
