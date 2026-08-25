pragma ComponentBehavior: Bound

import QtQuick

Item {
    id: measurementLayer

    required property var measurementController

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
