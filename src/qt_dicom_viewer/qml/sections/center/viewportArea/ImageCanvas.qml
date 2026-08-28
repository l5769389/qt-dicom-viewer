import QtQuick
import QtQuick.Layouts
import 'measurementLayer' as MeasurementLayer
import "../../../theme"

Rectangle {
    id: imageCanvasRoot
    required property var viewportController
    anchors.fill: parent
    color: viewportController
        ? viewportController.canvasBackgroundColor
        : Theme.canvasBackground
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
        if (!imageCanvasRoot.viewportController)
            return 1

        const physicalWidth =
            imageCanvasRoot.viewportController.imageColumns
            * imageCanvasRoot.viewportController.imageColumnSpacing

        const physicalHeight =
            imageCanvasRoot.viewportController.imageRows
            * imageCanvasRoot.viewportController.imageRowSpacing

        if (physicalWidth <= 0 || physicalHeight <= 0)
            return 1

        return Math.min(
            imageCanvasRoot.width / physicalWidth,
            imageCanvasRoot.height / physicalHeight
        )
    }

    // 图像场景使用毫米作为局部尺寸，负责整体平移、缩放和旋转。
    Item {
        id: imageScene
        readonly property var controller: imageCanvasRoot.viewportController

        readonly property real rowSpacing:
            controller ? controller.imageRowSpacing : 1.0
        readonly property real columnSpacing:
            controller ? controller.imageColumnSpacing : 1.0

        readonly property real physicalWidth:
            controller
                ? controller.imageColumns * columnSpacing
                : 0

        readonly property real physicalHeight:
            controller
                ? controller.imageRows * rowSpacing
                : 0

        width: physicalWidth
        height: physicalHeight


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


        // pixelLayer 保持一单位对应一个原始/重采样像素；spacingLayer
        // 再按毫米间距缩放，使非等距像素也能保持正确的物理宽高比例。
        Item {
            id: spacingLayer

            width: imageScene.controller
                ? imageScene.controller.imageColumns
                : 0
            height: imageScene.controller
                ? imageScene.controller.imageRows
                : 0

            transform: Scale {
                origin.x: 0
                origin.y: 0

                xScale: imageScene.columnSpacing
                yScale: imageScene.rowSpacing
            }
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
                        imageCanvasRoot.viewportController
                            ? imageCanvasRoot.viewportController.measurementController
                            : null
                }
            }
        }
    }

}
