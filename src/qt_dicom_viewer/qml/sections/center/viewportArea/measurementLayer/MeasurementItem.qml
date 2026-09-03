pragma ComponentBehavior: Bound
import QtQuick

Item {
    id: root
    objectName: "measurementItem"
    required property var measurement
    required property bool isDraft
    required property bool isSelected
    required property var coordinateMapper
    required property var transformState
    z: isSelected ? 2 : 1

    readonly property Item labelItem: root.measurement.type === "length"
        ? lengthItem.labelItem
        : root.measurement.type === "angle" ? angleItem.labelItem : roiItem.labelItem

    function labelHitRegion(targetItem) {
        if (root.isDraft || !root.visible || !root.labelItem || !root.labelItem.visible)
            return null
        // 标签处于不缩放的屏幕层；与 InteractionLayer 统一坐标，不能拿图像坐标判断。
        const position = root.labelItem.mapToItem(targetItem, 0, 0)
        return {
            measurementId: root.measurement.measurementId,
            x: position.x, y: position.y,
            width: root.labelItem.width, height: root.labelItem.height
        }
    }

    readonly property var mappedPoints: {
        // 显式依赖所有图像变换，mapToItem 本身不会建立这些属性的绑定。
        if (!root.transformState || !root.coordinateMapper)
            return []
        return (root.measurement.points ?? []).map(point =>
            root.coordinateMapper.mapDicomPixelToItem(root, point.column, point.row))
    }
    readonly property var corners: {
        if (!root.transformState || !root.coordinateMapper)
            return []
        const points = root.measurement.points ?? []
        if (points.length !== 2)
            return []
        const a = points[0], b = points[1]
        return [a, {column: b.column, row: a.row}, b, {column: a.column, row: b.row}].map(point =>
            root.coordinateMapper.mapDicomPixelToItem(root, point.column, point.row))
    }

    LengthMeasurementItem {
        id: lengthItem
        anchors.fill: parent
        visible: root.measurement.type === "length"
        measurement: root.measurement
        mappedPoints: root.mappedPoints
        isDraft: root.isDraft
        isSelected: root.isSelected
    }
    AngleMeasurementItem {
        id: angleItem
        anchors.fill: parent
        visible: root.measurement.type === "angle"
        measurement: root.measurement
        mappedPoints: root.mappedPoints
        isDraft: root.isDraft
        isSelected: root.isSelected
    }
    RoiMeasurementItem {
        id: roiItem
        anchors.fill: parent
        visible: root.measurement.type === "rect" || root.measurement.type === "ellipse"
        measurement: root.measurement
        corners: root.corners
        isDraft: root.isDraft
        isSelected: root.isSelected
    }
}
