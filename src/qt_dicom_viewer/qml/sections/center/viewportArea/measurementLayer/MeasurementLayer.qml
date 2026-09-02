pragma ComponentBehavior: Bound

import QtQuick

Item {
    id: measurementLayer

    required property var measurementController

    // 测量坐标属于无限延伸的图像坐标系，可以绘制到图像矩形之外。
    // 最外层 ImageCanvas 仍会将最终内容限制在整个视口画布内。
    clip: false

    Repeater {
        model: measurementLayer.measurementController
            ? measurementLayer.measurementController.measurementItems
            : []

        delegate: LengthMeasurementItem {
            required property var modelData
            isDraft: false
            isSelected: measurementLayer.measurementController
                ? modelData.measurementId
                    === measurementLayer.measurementController.selectedMeasurementId
                : false
            width: measurementLayer.width
            height: measurementLayer.height
            measurement: modelData
        }
    }

    LengthMeasurementItem {
        width: measurementLayer.width
        height: measurementLayer.height

        visible: measurementLayer.measurementController
                 && Object.keys(
                     measurementLayer.measurementController.activeTransaction
                 ).length > 0
        isDraft: true
        isSelected: false
        measurement: measurementLayer.measurementController
            ? measurementLayer.measurementController.activeTransaction
            : ({})
    }
}
