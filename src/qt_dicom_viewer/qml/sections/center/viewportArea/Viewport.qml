pragma
ComponentBehavior: Bound
import QtQuick
import "../../../theme"

Item {
    id: viewportRoot
    required property var viewportController
    required property bool hasTabs
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
        anchors.fill: parent
        z: 10
        anchors.margins: 8
        viewportController: viewportRoot.viewportController

    }

    DirectionOverlay {
        anchors.fill: parent
        z: 11

        directionLabels:
            viewportRoot.viewportController
                ? viewportRoot.viewportController.directionLabels
                : ({})
    }

    CrosshairLayer {
        anchors.fill: parent
        visible:
            imageCanvas.crosshairViewportPosition.x >= 0
            && imageCanvas.crosshairViewportPosition.y >= 0

        crosshairPosition:
            imageCanvas.crosshairViewportPosition
        crosshairStyle: viewportRoot.viewportController.crosshairStyle
        rotationDegrees:
            viewportRoot.viewportController
                ? viewportRoot.viewportController.crosshairRotationDegrees
                : 0
        z: 10
    }

    InteractionLayer {
        id: interactionLayer
        anchors.fill: parent
        z: 20
        enabled: viewportRoot.viewportController !== null
        crosshairHoverTarget:
            viewportRoot.viewportController
                ? viewportRoot.viewportController.crosshairHoverTarget
                : ""
        activeInteraction:
            viewportRoot.viewportController
                ? viewportRoot.viewportController.activeInteraction
                : ""

        onTapped: position => {
            if (!viewportRoot.viewportController)
                return

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
                lineTolerance
            )
        }

        onDragStarted: (startPosition, buttons) => {
            if (!viewportRoot.viewportController)
                return
            const hit = imageCanvas.mapToDicomPixel(
                interactionLayer,
                startPosition
            )
            const endpointTolerance =
                imageCanvas.pointHitToleranceInImagePixels

            const lineTolerance =
                imageCanvas.lineHitToleranceInImagePixels

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

}
