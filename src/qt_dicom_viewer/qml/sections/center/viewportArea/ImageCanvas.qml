import QtQuick
import QtQuick.Layouts
import 'measurementLayer' as MeasurementLayer
Rectangle {
    id: imageCanvasRoot
    required property var activeViewport
    anchors.fill: parent
    color: activeViewport
        ? activeViewport.canvasBackgroundColor
        : "#000000"
    clip: true

    function hitToleranceInImagePixels(screenTolerance,) {
        return screenTolerance / Math.max(
            Math.abs(imageScene.scale),
            0.0001
            )
    }

    function mapToDicomPixel(interactionLayer, position) {
        if (
            pixelLayer.width <= 0
            || pixelLayer.height <= 0
        ) {
            return {
                valid: false
            }
        }

        const local = pixelLayer.mapFromItem(
            interactionLayer,
            position.x,
            position.y
        )

        const inside =
            local.x >= 0
            && local.y >= 0
            && local.x < pixelLayer.width
            && local.y < pixelLayer.height

        if (!inside) {
            return {
                valid: false,
                column: local.x - 0.5,
                row: local.y - 0.5,
            }
        }

        return {
            valid: true,

            // 连续像素坐标，以第一颗像素中心为 (0, 0)
            column: local.x - 0.5,
            row: local.y - 0.5,

            clipColumn: Math.floor(Math.max(0, Math.min(pixelLayer.width - 1, local.x))),
            clipRow: Math.floor(Math.max(0, Math.min(pixelLayer.height - 1, local.y))),

            // 对应 PixelData 的整数索引
            columnIndex: Math.floor(local.x),
            rowIndex: Math.floor(local.y)
        }
    }

    readonly property real fitScale: {
        if (!imageCanvasRoot.activeViewport)
            return 1

        const columns =
            imageCanvasRoot.activeViewport.imageColumns
        const rows =
            imageCanvasRoot.activeViewport.imageRows

        if (columns <= 0 || rows <= 0)
            return 1

        return Math.min(
            imageCanvasRoot.width / columns,
            imageCanvasRoot.height / rows
        )
    }

    // 负责平移、缩放和旋转
    Item {
        id: imageScene

        readonly property var controller: imageCanvasRoot.activeViewport
        width: controller
            ? controller.imageColumns : 0
        height: controller
            ? controller.imageRows : 0

        // 未缩放时让图像中心位于 viewport 中心
        x: (
            imageCanvasRoot.width - width
        ) / 2 + (
            controller ? controller.panX : 0
        )

        y: (
            imageCanvasRoot.height - height
        ) / 2 + (
            controller ? controller.panY : 0
        )

        transformOrigin: Item.Center

        scale: imageCanvasRoot.fitScale * (
            controller ? controller.zoom : 1
        )

        rotation: controller
            ? controller.rotationDegrees : 0

        // 负责水平、垂直翻转
        Item {
            id: pixelLayer
            anchors.fill: parent

            transform: Scale {
                origin.x
                    :
                    pixelLayer.width / 2
                origin.y
                    :
                    pixelLayer.height / 2

                xScale: imageScene.controller
                    && imageScene.controller.horizontalFlip
                    ? -1 : 1

                yScale: imageScene.controller
                    && imageScene.controller.verticalFlip
                    ? -1 : 1
            }

            Image {
                anchors.fill: parent

                source: imageScene.controller ? imageScene.controller.imageSource : ""

                // pixelLayer 的宽高已经保持图像比例
                fillMode: Image.Stretch
                cache: false
                smooth: true
            }

            MeasurementLayer.MeasurementLayer {
                anchors.fill: parent
                measurementController:
                    imageCanvasRoot.activeViewport
                        ? imageCanvasRoot.activeViewport.measurementController
                        : null
            }
        }
    }

}
