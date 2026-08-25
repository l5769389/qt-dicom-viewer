pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "../../../theme"

Item {
    id: viewportLayout

    required property var viewportController
    required property var currentTabAllViewports
    required property string tabType
    required property bool hasTabs

    signal viewportActivated(var viewport_id)

    GridLayout {
        anchors.fill: parent

        columns: viewportLayout.tabType === "mpr" ? 2 : 1
        rows: viewportLayout.tabType === "mpr" ? 2 : 1
        uniformCellWidths: true
        uniformCellHeights: true

        columnSpacing: 2
        rowSpacing: 2

        Repeater {
            model: viewportLayout.currentTabAllViewports

            delegate: Rectangle {
                id: viewportCell

                required property var modelData
                readonly property string viewportType:
                    viewportCell.modelData
                        ? viewportCell.modelData.viewportType
                        : ""
                readonly property bool isActive:
                    viewportCell.modelData
                        === viewportLayout.viewportController

                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.row: {
                    if (viewportLayout.tabType !== "mpr")
                        return 0

                    return viewportCell.viewportType === "sagittal" ? 1 : 0
                }
                Layout.column: {
                    if (viewportLayout.tabType !== "mpr")
                        return 0

                    return viewportCell.viewportType === "coronal" ? 1 : 0
                }
                Layout.rowSpan:
                    viewportLayout.tabType === "mpr"
                    && viewportCell.viewportType === "coronal"
                        ? 2
                        : 1

                color: Theme.canvasBackground
                border.width: viewportCell.isActive ? 2 : 1
                border.color: viewportCell.isActive
                    ? Theme.selectionBorder
                    : Theme.borderSubtle

                Behavior on border.color {
                    ColorAnimation { duration: 100 }
                }

                Viewport {
                    anchors.fill: parent
                    anchors.margins: 2

                    viewportController: viewportCell.modelData
                    hasTabs: true
                }

                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top

                    visible: viewportCell.isActive
                    height: 2
                    color: Theme.activeIndicator
                    z: 30
                }

                TapHandler {
                    id: activationHandler

                    onPressedChanged: {
                        if (activationHandler.pressed) {
                            viewportLayout.viewportActivated(
                                viewportCell.modelData.viewportId
                            )
                        }
                    }
                }
            }
        }
    }
}
