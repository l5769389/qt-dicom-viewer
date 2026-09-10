pragma
ComponentBehavior: Bound
import QtQuick
import "../../../theme"

Item {
    id: viewportRoot
    property bool multiViewport: false
    property bool anonymousExport: false
    required property var viewportController
    required property bool hasTabs
    Keys.onEscapePressed: event => {
        if (viewportRoot.viewportController && viewportRoot.viewportController.reconstructionController)
            viewportRoot.viewportController.reconstructionController.setRegistrationActive(false)
        if (viewportRoot.viewportController)
            viewportRoot.viewportController.cancelMeasurement()
        event.accepted = true
    }
    Keys.onDeletePressed: event => {
        if (viewportRoot.viewportController)
            viewportRoot.viewportController.deleteSelectedMeasurement()
        event.accepted = true
    }
    Keys.onPressed: event => {
        if (event.matches(StandardKey.Copy)) {
            event.accepted = viewportRoot.viewportController?.copySelectedAnnotation() ?? false
            return
        }
        if (event.matches(StandardKey.Paste)) {
            event.accepted = viewportRoot.viewportController?.pasteAnnotation() ?? false
            return
        }
        if (event.key === Qt.Key_Backspace && viewportRoot.viewportController) {
            viewportRoot.viewportController.deleteSelectedMeasurement()
            event.accepted = true
        }
    }
    readonly property bool isMprViewport:
        viewportRoot.viewportController
        && ["axial", "sagittal", "coronal"].indexOf(
            viewportRoot.viewportController.viewportType
        ) >= 0


    function syncViewportSize() {
        if (!viewportRoot.viewportController)
            return

        viewportRoot.viewportController.setViewportSize(
            viewportRoot.width,
            viewportRoot.height
        )
    }

    function getCrosshairPosition() {
        const mpr_planes = ['axial', 'sagittal', 'coronal']
        if (
            !viewportRoot.viewportController
            || mpr_planes.indexOf(
                viewportRoot.viewportController.viewportType
            ) < 0
        ) {
            return
        }
        const position = viewportRoot.viewportController.crosshairPosition

        if (position.centerX === null || position.centerY === null) {
            return Qt.point(viewportRoot.width / 2, viewportRoot.height / 2)
        } else {
            return Qt.point(viewportRoot.viewportController.centerX, viewportRoot.viewportController.centerY)
        }
    }


    onWidthChanged: syncViewportSize()
    onHeightChanged: syncViewportSize()
    onViewportControllerChanged: syncViewportSize()
    onVisibleChanged: {
        if (!visible && viewportRoot.viewportController)
            viewportRoot.viewportController.activeAnnotationController.clearHover()
    }

    Component.onCompleted: syncViewportSize()

    // 显示影像
    ImageCanvas {
        id: imageCanvas
        anchors.fill: parent
        z: 0
        viewportController: viewportRoot.viewportController
    }

    // 显示空白提示信息
    Column {
        id: emptyView
        anchors.centerIn: parent
        spacing: 6
        visible: !viewportRoot.hasTabs

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "No viewportRoot open"
            color: Theme.textMuted
            font.pixelSize: 16
            font.weight: Font.DemiBold
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Select a series from the left panel"
            color: Theme.textDisabled
            font.pixelSize: 12
        }
    }

    // 四角信息
    Overlay {
        id: metadataOverlay
        multiViewport: viewportRoot.multiViewport
        anchors.fill: parent
        z: 10
        anchors.margins: 8
        viewportController: viewportRoot.viewportController
        visible: !viewportRoot.anonymousExport && (viewportRoot.viewportController
            ? viewportRoot.viewportController.showWindowAnnotations : false)
        hideSensitiveInfo: viewportRoot.viewportController
            ? viewportRoot.viewportController.hideSensitiveInfo : false

    }

    ScaleBar {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.bottomMargin: metadataOverlay.visible && metadataOverlay.petWorkspace
            ? Math.max(32, metadataOverlay.bottomTextHeight + 20) : 32
        z: 11
        pixelsPerMm: imageCanvas.pixelsPerMillimeter
        visible: viewportRoot.viewportController?.showScaleBar === true && lengthMm > 0
        calibrated: viewportRoot.viewportController?.hasPhysicalSpacing ?? false
        options: viewportRoot.viewportController?.settingsController.values.scale ?? ({})
    }

    DirectionOverlay {
        anchors.fill: parent
        z: 11
        visible: viewportRoot.viewportController
            ? viewportRoot.viewportController.showDicomOverlay : false

        directionLabels:
            viewportRoot.viewportController
                ? viewportRoot.viewportController.directionLabels
                : ({})
    }

    MprSlabGuideLayer {
        anchors.fill: parent
        z: 9
        visible: viewportRoot.isMprViewport
            && viewportRoot.viewportController.showLocalizer
            && guides.length > 0
        coordinateMapper: imageCanvas
        transformState: imageCanvas.measurementTransformState
        guides: viewportRoot.isMprViewport
            && viewportRoot.viewportController
            ? viewportRoot.viewportController.mprSlabGuides
            : []
    }

    CrosshairLayer {
        anchors.fill: parent
        visible:
            viewportRoot.viewportController
            && viewportRoot.viewportController.showLocalizer
            && viewportRoot.viewportController.hasCrosshair
            && Number.isFinite(imageCanvas.crosshairViewportPosition.x)
            && Number.isFinite(imageCanvas.crosshairViewportPosition.y)

        crosshairPosition:
            imageCanvas.crosshairViewportPosition
        crosshairStyle: viewportRoot.viewportController
            ? viewportRoot.viewportController.crosshairStyle : ({})
        rotationDegrees:
            viewportRoot.viewportController
                ? viewportRoot.viewportController.crosshairRotationDegrees
                : 0
        z: 10
    }

    TextAnnotationLayer {
        hideText: viewportRoot.anonymousExport
        preferences: viewportRoot.viewportController?.settingsController.values ?? ({})
        anchors.fill: parent
        z: 14
        annotationController: viewportRoot.viewportController
            ? viewportRoot.viewportController.textAnnotationController : null
        coordinateMapper: imageCanvas
        transformState: imageCanvas.measurementTransformState
    }

    ColorBar {
        id: viewportColorBar
        readonly property bool avoidCornerText: metadataOverlay.visible && metadataOverlay.petWorkspace
        readonly property real topInset: avoidCornerText ? metadataOverlay.topLeftTextHeight + 20 : 0
        readonly property real bottomInset: avoidCornerText ? metadataOverlay.bottomLeftTextHeight + 20 : 0
        anchors.left: parent.left
        anchors.leftMargin: 14
        height: Math.max(0, Math.min(230, parent.height * 0.42, parent.height - topInset - bottomInset))
        y: Math.max(topInset, Math.min((parent.height - height) / 2, parent.height - bottomInset - height))
        z: 15
        visible: viewportRoot.viewportController?.showColorBar === true && height >= 32
        stops: viewportRoot.viewportController
            ? viewportRoot.viewportController.activeColorMapStops : []
        minimumValue: viewportRoot.viewportController
            ? viewportRoot.viewportController.displayRangeMinimum : 0
        maximumValue: viewportRoot.viewportController
            ? viewportRoot.viewportController.displayRangeMaximum : 255
    }

    InteractionLayer {
        id: interactionLayer
        anchors.fill: parent
        z: 20
        enabled: viewportRoot.viewportController !== null
        onPointerPressedAt: (position, buttons) => {
            const controller = viewportRoot.viewportController
            if (controller?.captureLocatorPress === undefined) return
            const hit = imageCanvas.mapToDicomPixel(interactionLayer, position)
            interactionLayer.locatorPressed = controller.captureLocatorPress(
                position.x, position.y, buttons, hit.valid, hit.column, hit.row,
                imageCanvas.pointHitToleranceInImagePixels, imageCanvas.lineHitToleranceInImagePixels)
        }
        onPointerTapFinished: viewportRoot.viewportController?.clearLocatorPress?.()
        registrationInteraction: viewportRoot.viewportController !== null
            && viewportRoot.viewportController.reconstructionController?.registrationActive === true
            && ["pet", "fusion"].includes(viewportRoot.viewportController.viewportRole)
        crosshairHoverTarget:
            viewportRoot.viewportController
                ? viewportRoot.viewportController.crosshairHoverTarget
                : ""
        activeInteraction:
            viewportRoot.viewportController
                ? viewportRoot.viewportController.activeInteraction
                : ""
        measurementCursorKind:
            viewportRoot.viewportController
                ? (activeInteraction === "service:qa" && viewportRoot.viewportController.qaController
                    ? viewportRoot.viewportController.qaController.hoverCursorKind
                    : viewportRoot.viewportController.activeAnnotationController.hoverCursorKind)
                : ""
        regionCursorKind: viewportRoot.viewportController?.regionCursorKind ?? ""

        onPointerExited: {
            viewportRoot.viewportController?.clearInteractionHover()
        }

        onTapped: position => {
            viewportRoot.forceActiveFocus()
            if (!viewportRoot.viewportController)
                return

            imageCanvas.updateMeasurementHitRegions(interactionLayer)
            const hit = imageCanvas.mapToDicomPixel(
                interactionLayer,
                position
            )
            const endpointTolerance =
                imageCanvas.pointHitToleranceInImagePixels
            const lineTolerance =
                imageCanvas.lineHitToleranceInImagePixels

            viewportRoot.viewportController.selectMeasurementAt(
                hit.valid,
                hit.column,
                hit.row,
                endpointTolerance,
                lineTolerance,
                position.x,
                position.y
            )
        }

        onDragStarted: (startPosition, buttons) => {
            viewportRoot.forceActiveFocus()
            if (!viewportRoot.viewportController)
                return
            imageCanvas.updateMeasurementHitRegions(interactionLayer)
            const hit = imageCanvas.mapToDicomPixel(
                interactionLayer,
                startPosition
            )
            const endpointTolerance =
                imageCanvas.pointHitToleranceInImagePixels

            const lineTolerance =
                imageCanvas.lineHitToleranceInImagePixels

            // 按下前可能没有 move 事件，按本次拖动起点确认光标，再锁定到本次拖动。
            viewportRoot.viewportController.refreshInteractionHover(
                startPosition.x, startPosition.y, hit.column, hit.row,
                endpointTolerance, lineTolerance
            )
            interactionLayer.dragCursorKind = interactionLayer.hoverCursorKind
            viewportRoot.viewportController.beginInteraction(
                startPosition.x,
                startPosition.y,
                buttons,
                hit.valid,
                hit.column,
                hit.row,
                endpointTolerance,
                lineTolerance
            )
        }

        onDragMoved: (
            startPosition,
            currentPosition,
            stepDelta,
            totalDelta
        ) => {
            if (!viewportRoot.viewportController)
                return
            const hit = imageCanvas.mapToDicomPixel(
                interactionLayer,
                currentPosition
            )
            if (viewportRoot.viewportController.updateRegistrationDrag !== undefined
                    && viewportRoot.viewportController.updateRegistrationDrag(hit.column, hit.row))
                return
            viewportRoot.viewportController.updateInteraction(
                startPosition,
                currentPosition,
                stepDelta,
                totalDelta,
                hit.valid,
                hit.column,
                hit.row
            )
        }

        onDragFinished: (
            startPosition,
            endPosition,
            totalDelta
        ) => {
            if (!viewportRoot.viewportController)
                return
            const hit = imageCanvas.mapToDicomPixel(
                interactionLayer,
                endPosition
            )
            viewportRoot.viewportController.endInteraction(
                endPosition.x,
                endPosition.y,
                hit.valid,
                hit.column,
                hit.row
            )
            imageCanvas.updateMeasurementHitRegions(interactionLayer)
            viewportRoot.viewportController.refreshInteractionHover(
                endPosition.x, endPosition.y, hit.column, hit.row,
                imageCanvas.pointHitToleranceInImagePixels,
                imageCanvas.lineHitToleranceInImagePixels
            )
        }

        onWheelMoved: (
            position,
            angleDeltaY,
            pixelDeltaY,
            modifiers
        ) => {
            if (!viewportRoot.viewportController)
                return

            viewportRoot.viewportController.handleWheel(
                angleDeltaY,
                pixelDeltaY,
                position.x,
                position.y,
                modifiers
            )
        }

        onPointerMoved: position => {
            if (!viewportRoot.viewportController)
                return

            imageCanvas.updateMeasurementHitRegions(interactionLayer)
            const hit = imageCanvas.mapToDicomPixel(
                interactionLayer,
                position
            )
            viewportRoot.viewportController.updateCursorPosition(
                position.x,
                position.y,
                hit.column,
                hit.row,
                hit.clipColumn,
                hit.clipRow,
                hit.valid,
                imageCanvas.pointHitToleranceInImagePixels,
                imageCanvas.lineHitToleranceInImagePixels
            )
        }
    }

    Rectangle {
        id: quantificationWarning
        readonly property string message: !viewportRoot.viewportController ? ""
            : viewportRoot.viewportController.errorMessage !== ""
            ? "显示更新失败，保留上一帧：" + viewportRoot.viewportController.errorMessage
            : viewportRoot.viewportController.quantificationWarning !== ""
            ? "PET 提示：" + viewportRoot.viewportController.quantificationWarning
            : viewportRoot.viewportController.reconstructionController
            ? viewportRoot.viewportController.reconstructionController.warning : ""
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 18
        z: 29
        visible: viewportRoot.viewportController
            && viewportRoot.viewportController.loadState === "ready"
            && message !== ""
        width: Math.min(parent.width - 48, warningText.implicitWidth + 28)
        height: warningText.implicitHeight + 18
        radius: 6
        color: Theme.panelBackgroundStrong
        border.color: Theme.warningColor

        Text {
            id: warningText
            anchors.centerIn: parent
            width: Math.min(implicitWidth, quantificationWarning.width - 28)
            text: quantificationWarning.message
            color: Theme.warningColor
            font.pixelSize: 12
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
        }
    }

    Rectangle {
        anchors.fill: parent
        z: 30
        visible: viewportRoot.viewportController
            && viewportRoot.viewportController.loadState === "error"
        color: Theme.canvasBackground

        Column {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 520)
            spacing: 10

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "无法显示 2D 影像"
                color: Theme.warningColor
                font.pixelSize: 16
                font.weight: Font.DemiBold
            }

            Text {
                width: parent.width
                text: viewportRoot.viewportController
                    ? viewportRoot.viewportController.errorMessage
                    : ""
                color: Theme.textMuted
                font.pixelSize: 12
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
            }
        }
    }

}
