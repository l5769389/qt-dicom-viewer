pragma
ComponentBehavior: Bound

import QtQuick

Item {
    id: interactionLayer

    signal pointerMoved(point position)

    signal dragStarted(
        point startPosition,
        int buttons
    )

    signal dragMoved(
        point startPosition,
        point currentPosition,
        point stepDelta,
        point totalDelta
    )

    signal dragFinished(
        point startPosition,
        point endPosition,
        point totalDelta
    )

    signal wheelMoved(
        point position,
        real angleDeltaY,
        real pixelDeltaY,
        int modifiers
    )

    property point dragStart: Qt.point(0, 0)
    property point lastPosition: Qt.point(0, 0)

    HoverHandler {
        id: hoverHandler

        acceptedDevices: PointerDevice.Mouse
            | PointerDevice.TouchPad

        cursorShape: dragHandler.active
            ? Qt.ClosedHandCursor
            : Qt.CrossCursor

        onPointChanged: {
            if (hoverHandler.hovered) {
                interactionLayer.pointerMoved(
                    hoverHandler.point.position
                )
            }
        }
    }

    DragHandler {
        id: dragHandler

        target: null
        dragThreshold: 0
        acceptedButtons: Qt.LeftButton
            | Qt.RightButton
            | Qt.MiddleButton

        onActiveChanged: {
            if (dragHandler.active) {
                interactionLayer.dragStart =
                    dragHandler.centroid.pressPosition

                interactionLayer.lastPosition =
                    dragHandler.centroid.position

                interactionLayer.dragStarted(
                    interactionLayer.dragStart,
                    dragHandler.centroid.pressedButtons
                )
            } else {
                interactionLayer.dragFinished(
                    interactionLayer.dragStart,
                    dragHandler.centroid.position,
                    dragHandler.activeTranslation
                )
            }
        }

        onActiveTranslationChanged: {
            if (!dragHandler.active)
                return

            const current = dragHandler.centroid.position
            const step = Qt.point(
                current.x - interactionLayer.lastPosition.x,
                current.y - interactionLayer.lastPosition.y
            )

            interactionLayer.dragMoved(
                interactionLayer.dragStart,
                current,
                step,
                dragHandler.activeTranslation
            )

            interactionLayer.lastPosition = current
        }
    }

    WheelHandler {
    id: wheelHandler

    target: null
    orientation: Qt.Vertical
    blocking: true

    acceptedDevices: PointerDevice.Mouse
                   | PointerDevice.TouchPad

    onWheel: wheelEvent => {
        interactionLayer.wheelMoved(
            Qt.point(wheelEvent.x, wheelEvent.y),
            wheelEvent.angleDelta.y,
            wheelEvent.pixelDelta.y,
            Number(wheelEvent.modifiers)
        )

        // 已处理事件，不再继续传递给下面的组件。
        wheelEvent.accepted = true
    }
}
}