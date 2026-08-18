import QtQuick
import QtQuick.Layouts

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
        anchors.margins: 8
        activeViewport: viewportRoot.activeViewport
    }

    Column {
        id: emptyView
        anchors.centerIn: parent
        spacing: 6
        visible: !hasTabs

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "No viewportRoot open"
            color: "#778392"
            font.pixelSize: 16
            font.weight: Font.DemiBold
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Select a series from the left panel"
            color: "#505a67"
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

        onDragStarted: (startPosition, buttons) => {
            if (!viewportRoot.activeViewport)
                return

            viewportRoot.activeViewport.beginInteraction(
                startPosition.x,
                startPosition.y,
                buttons
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

            viewportRoot.activeViewport.updateInteraction(
                startPosition,
                currentPosition,
                stepDelta,
                totalDelta
            )
        }

        onDragFinished: (
            startPosition,
            endPosition,
            totalDelta
        ) => {
            if (!viewportRoot.activeViewport)
                return

            viewportRoot.activeViewport.endInteraction(
                endPosition.x,
                endPosition.y
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
                return
            }

            viewportRoot.activeViewport.updateCursorPosition(
                hit.column,
                hit.row,
                hit.clipColumn,
                hit.clipRow,
                hit.columnIndex,
                hit.rowIndex
            )
        }

    }
}