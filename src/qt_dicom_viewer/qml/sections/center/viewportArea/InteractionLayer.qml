pragma
ComponentBehavior: Bound

import QtQuick
import QtQuick.Shapes
import "../../../components" as Components
import "../../../theme"

Item {
    id: interactionLayer
    objectName: "viewportInteractionLayer"
    clip: true

    signal pointerMoved(point position)
    signal pointerExited()

    signal tapped(point position)

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
    property string crosshairHoverTarget: ""
    property string measurementCursorKind: ""
    property string activeInteraction: ""
    property string dragCursorKind: ""
    // 从按下到释放持续为 true，不受 DragHandler 拖动阈值影响。
    readonly property bool pointerPressed: pressTracker.active

    function cursorKindForInteraction(interaction) {
        switch (interaction) {
            case "window":
                return "window"
            case "scroll":
                return "scroll"
            case "pan":
                return "pan"
            case "zoom":
                return "zoom"
            case "mpr:rotate3d":
                return "rotate-3d"
            default:
                return ""
        }
    }

    readonly property string hoverCursorKind:
            crosshairHoverTarget === "center"
        ? "pan"
        : crosshairHoverTarget === "horizontalLine"
            || crosshairHoverTarget === "verticalLine"
            ? "rotate-3d-variant"
            : activeInteraction.startsWith("measure:") && measurementCursorKind !== ""
                ? measurementCursorKind
                : cursorKindForInteraction(activeInteraction)

    readonly property string effectiveCursorKind:
        dragHandler.active
            ? dragCursorKind
            : hoverCursorKind

    readonly property bool customCursorActive:
        effectiveCursorKind !== ""

    readonly property point cursorPosition:
        dragHandler.active
            ? dragHandler.centroid.position
            : hoverHandler.point.position

    // 作用只有一个：稳定判断鼠标是否处于“按下到释放”的周期。
    // 鼠标按下       pressTracker.active = true
    // 按住并移动     pressTracker.active = true
    // 进入 Drag      pressTracker.active = true
    // 鼠标释放       pressTracker.active = false
    PointHandler {
        id: pressTracker

        target: null
        acceptedDevices: PointerDevice.Mouse
            | PointerDevice.TouchPad
        acceptedButtons: Qt.LeftButton
            | Qt.RightButton
            | Qt.MiddleButton
    }

    HoverHandler {
        id: hoverHandler

        acceptedDevices: PointerDevice.Mouse
            | PointerDevice.TouchPad

        cursorShape: {
            if (interactionLayer.customCursorActive)
                return Qt.BlankCursor
            return Qt.CrossCursor
        }

        onHoveredChanged: {
            if (!hovered)
                interactionLayer.pointerExited()
        }

        onPointChanged: {
            if (
                !hoverHandler.hovered
                || interactionLayer.pointerPressed
            )
                return

            interactionLayer.pointerMoved(
                hoverHandler.point.position
            )
        }
    }

    Item {
        id: customCursor
        objectName: "viewportCustomCursor"

        readonly property real pointerHeight: 20
        readonly property real pointerScale: pointerHeight / 30
        readonly property real operationIconSize: 20

        // 箭头尖端是热点；操作图标紧贴箭头右下方。
        x: interactionLayer.cursorPosition.x - 2 * pointerScale
        y: interactionLayer.cursorPosition.y - 1.5 * pointerScale
        z: 100

        width: cursorBadge.x + cursorBadge.width
        height: Math.max(pointerHeight, cursorBadge.y + cursorBadge.height)
        visible:
            (hoverHandler.hovered || dragHandler.active)
            && interactionLayer.customCursorActive

        Rectangle {
            id: cursorBadge
            objectName: "viewportCursorBadge"
            x: 10
            y: 6
            width: customCursor.operationIconSize + 6
            height: width
            radius: 4
            color: Qt.rgba(
                Theme.panelBackgroundStrong.r,
                Theme.panelBackgroundStrong.g,
                Theme.panelBackgroundStrong.b,
                0.72
            )

            Components.AppIcon {
                objectName: "viewportCursorOperationIcon"
                anchors.centerIn: parent
                iconName: interactionLayer.effectiveCursorKind
                iconSize: customCursor.operationIconSize
                iconColor: "#ffffff"
            }
        }

        Shape {
            objectName: "viewportCursorPointer"
            width: 22
            height: 30
            antialiasing: true
            // PathSvg 不会随 Shape 的宽高自动缩放，显式缩放路径和描边。
            transform: Scale {
                xScale: customCursor.pointerScale
                yScale: customCursor.pointerScale
            }

            ShapePath {
                fillColor: "#ffffff"
                strokeColor: "#101820"
                strokeWidth: 1.5
                joinStyle: ShapePath.RoundJoin

                PathSvg {
                    path: "M2,1.5V23.5L7.6,18.3L12.3,28.5L16.5,26.5L11.8,16.6H20Z"
                }
            }
        }
    }

    TapHandler {
        id: pressHandler

        acceptedButtons: Qt.LeftButton
            | Qt.RightButton
            | Qt.MiddleButton


        onTapped: (eventPoint, button) => {
            // 只有左键点击执行测量选择等 tapped 逻辑。
            if (button !== Qt.LeftButton)
                return

            interactionLayer.tapped(
                eventPoint.position
            )
        }
    }

    DragHandler {
        id: dragHandler

        target: null
        acceptedButtons: Qt.LeftButton
            | Qt.RightButton
            | Qt.MiddleButton

        onActiveChanged: {
            if (dragHandler.active) {
                interactionLayer.dragCursorKind =
                    interactionLayer.hoverCursorKind

                interactionLayer.dragStart =
                    dragHandler.centroid.pressPosition

                interactionLayer.lastPosition =
                    dragHandler.centroid.position

                interactionLayer.dragStarted(
                    interactionLayer.dragStart,
                    dragHandler.centroid.pressedButtons
                )
            } else {
                interactionLayer.dragCursorKind = ""

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
