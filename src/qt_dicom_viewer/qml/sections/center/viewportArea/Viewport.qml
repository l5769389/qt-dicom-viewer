import QtQuick
import QtQuick.Layouts

Item {
    id: viewport
    required property var activeViewport
    required property bool hasTabs

    function syncViewportSize() {
        if (!viewport.activeViewport)
            return

        viewport.activeViewport.setViewportSize(
            viewport.width,
            viewport.height
        )
    }

    onWidthChanged: syncViewportSize()
    onHeightChanged: syncViewportSize()
    onActiveViewportChanged: syncViewportSize()

    Component.onCompleted: syncViewportSize()
    Rectangle {
        id: viewportArea
        anchors.fill: parent
        color: "#080a0d"
        clip: true

        DicomImage {
            anchors.fill: parent
            z: 0
            anchors.margins: 8
            activeViewport: viewport.activeViewport
        }

        Column {
            anchors.centerIn: parent
            spacing: 6
            visible: !hasTabs

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "No viewport open"
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
            activeViewport: viewport.activeViewport

        }

        InteractionLayer {
            anchors.fill: parent
            z: 20
            enabled: viewport.activeViewport !== null

            onDragStarted: (startPosition, buttons) => {
                if (!viewport.activeViewport)
                    return

                viewport.activeViewport.beginInteraction(
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
                if (!viewport.activeViewport)
                    return

                viewport.activeViewport.updateInteraction(
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
                if (!viewport.activeViewport)
                    return

                viewport.activeViewport.endInteraction(
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
                if (!viewport.activeViewport)
                    return

                viewport.activeViewport.handleWheel(
                    angleDeltaY,
                    pixelDeltaY,
                    position.x,
                    position.y,
                    modifiers
                )
            }

        }
    }
}