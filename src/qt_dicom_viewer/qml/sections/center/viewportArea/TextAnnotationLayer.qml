pragma ComponentBehavior: Bound

import QtQuick
import "../../../theme"

Item {
    id: annotationLayer
    objectName: "textAnnotationLayer"
    required property var annotationController
    required property var coordinateMapper
    required property var transformState

    Repeater {
        model: annotationLayer.annotationController
            ? annotationLayer.annotationController.annotationItems : []

        delegate: Rectangle {
            id: annotationItem
            required property var modelData
            readonly property point screenPoint: {
                const dependency = annotationLayer.transformState
                    ? annotationLayer.transformState.join("|") : ""
                if (!dependency || !annotationLayer.coordinateMapper)
                    return Qt.point(-1000, -1000)
                return annotationLayer.coordinateMapper.mapDicomPixelToItem(
                    annotationLayer,
                    modelData.column,
                    modelData.row
                )
            }

            objectName: "textAnnotation-" + modelData.annotationId
            x: screenPoint.x + 5
            y: screenPoint.y - height - 5
            width: annotationText.implicitWidth + 10
            height: annotationText.implicitHeight + 6
            radius: 3
            color: modelData.selected ? "#990b1b27" : "#6602070e"
            border.color: modelData.selected
                ? Theme.selectionBorder : "transparent"
            border.width: modelData.selected ? 1 : 0

            Text {
                id: annotationText
                anchors.centerIn: parent
                text: annotationItem.modelData.text
                color: annotationItem.modelData.color
                font.pixelSize: annotationItem.modelData.fontSize
                font.weight: Font.DemiBold
                style: Text.Outline
                styleColor: Theme.overlayOutline
            }
        }
    }
}
