import QtQuick
import "../../../theme"

Item {
    id: viewportRoot
    required property var activeViewport
    required property bool hasTabs

    function syncViewportSize() {
        if (!viewportRoot.activeViewport)
            return

        viewportRoot.activeViewport.setViewportSize(
            viewportRoot.width,
            viewportRoot.height
        )
    }


    onWidthChanged: syncViewportSize()
    onHeightChanged: syncViewportSize()
    onActiveViewportChanged: syncViewportSize()

    Component.onCompleted: syncViewportSize()

    ImageCanvas {
        id: imageCanvas
        anchors.fill: parent
        z: 0
        activeViewport: viewportRoot.activeViewport
    }

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

    Overlay {
        anchors.fill: parent
        z: 10
        anchors.margins: 8
        activeViewport: viewportRoot.activeViewport

    }

    InteractionLayer {
        id: interactionLayer
        anchors.fill: parent
        z: 20
        enabled: viewportRoot.activeViewport !== null

        onTapped: position => {
            if (!viewportRoot.activeViewport)
                return

            const hit = imageCanvas.mapToDicomPixel(
                interactionLayer,
                position
            )
            const endpointTolerance =
                imageCanvas.hitToleranceInImagePixels(8)
            const lineTolerance =
                imageCanvas.hitToleranceInImagePixels(6)

            viewportRoot.activeViewport.selectMeasurementAt(
                hit.valid,
                hit.column,
                hit.row,
                endpointTolerance,
                lineTolerance
            )
        }

        onDragStarted: (startPosition, buttons) => {
            if (!viewportRoot.activeViewport)
                return
            const hit = imageCanvas.mapToDicomPixel(
                interactionLayer,
                startPosition
            )
            const endpointTolerance = imageCanvas.hitToleranceInImagePixels(8)

            const lineTolerance = imageCanvas.hitToleranceInImagePixels(6)

            viewportRoot.activeViewport.beginInteraction(
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
            if (!viewportRoot.activeViewport)
                return
            const hit = imageCanvas.mapToDicomPixel(
                interactionLayer,
                currentPosition
            )
            viewportRoot.activeViewport.updateInteraction(
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
            if (!viewportRoot.activeViewport)
                return
            const hit = imageCanvas.mapToDicomPixel(
                interactionLayer,
                endPosition
            )
            viewportRoot.activeViewport.endInteraction(
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
            if (!viewportRoot.activeViewport)
                return

            viewportRoot.activeViewport.handleWheel(
                angleDeltaY,
                pixelDeltaY,
                position.x,
                position.y,
                modifiers
            )
        }

        onPointerMoved: position => {
            if (!viewportRoot.activeViewport)
                return

            const hit = imageCanvas.mapToDicomPixel(
                interactionLayer,
                position
            )

            if (!hit.valid) {
                return;
            }

            viewportRoot.activeViewport.updateCursorPosition(
                hit.column,
                hit.row,
                hit.clipColumn,
                hit.clipRow,
                hit.valid,
                hit.columnIndex,
                hit.rowIndex
            )
        }

    }
}
