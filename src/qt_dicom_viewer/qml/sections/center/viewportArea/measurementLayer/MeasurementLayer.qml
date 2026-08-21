import QtQuick
import QtQuick.Shapes

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
                     measurementLayer.measurementController.draftItem
                 ).length > 0
        isDraft: true
        measurement: measurementLayer.measurementController
            ? measurementLayer.measurementController.draftItem
            : ({})
    }
}