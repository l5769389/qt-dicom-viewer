pragma
ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "../../../theme"

Item {
    id: viewportLayout

    required property var viewportController
    required property var currentTabAllViewports
    required property string tabType
    required property bool hasTabs
    property string layoutMode: "grid"
    property string focusedViewportId: ""
    readonly property bool singleViewMode:
        layoutMode === "single" && focusedViewportId !== ""
    readonly property var mprPlacements: ({
        "axial": {
            "row": 0,
            "column": 0,
            "rowSpan": 1,
            "columnSpan": 1
        },
        "sagittal": {
            "row": 1,
            "column": 0,
            "rowSpan": 1,
            "columnSpan": 1
        },
        "coronal": {
            "row": 0,
            "column": 1,
            "rowSpan": 2,
            "columnSpan": 1
        }
    })

    signal viewportActivated(var viewport_id)

    function resetLayout() {
        viewportLayout.layoutMode = "grid"
        viewportLayout.focusedViewportId = ""
    }

    function toggleSingleView(viewportId) {
        if (viewportLayout.currentTabAllViewports.length <= 1)
            return

        viewportLayout.viewportActivated(viewportId)
        if (
            viewportLayout.singleViewMode
            && viewportLayout.focusedViewportId === viewportId
        ) {
            viewportLayout.resetLayout()
            return
        }

        viewportLayout.focusedViewportId = viewportId
        viewportLayout.layoutMode = "single"
    }

    function placementFor(viewportId, viewportType) {
        if (viewportLayout.singleViewMode) {
            return {
                "visible": viewportId
                    === viewportLayout.focusedViewportId,
                "row": 0,
                "column": 0,
                "rowSpan": viewportGrid.rows,
                "columnSpan": viewportGrid.columns
            }
        }

        const placement = viewportLayout.tabType === "mpr"
            ? viewportLayout.mprPlacements[viewportType]
            : null
        return {
            "visible": true,
            "row": placement ? placement.row : 0,
            "column": placement ? placement.column : 0,
            "rowSpan": placement ? placement.rowSpan : 1,
            "columnSpan": placement ? placement.columnSpan : 1
        }
    }

    onCurrentTabAllViewportsChanged: resetLayout()
    onTabTypeChanged: resetLayout()

    GridLayout {
        id: viewportGrid

        anchors.fill: parent

        columns: viewportLayout.tabType === "mpr" ? 2 : 1
        rows: viewportLayout.tabType === "mpr" ? 2 : 1
        uniformCellWidths: true
        uniformCellHeights: true

        columnSpacing: 2
        rowSpacing: 2

        Repeater {
            model: viewportLayout.currentTabAllViewports

            delegate: Item {
                id: viewportCell

                required property var modelData
                readonly property string viewportType:
                    viewportCell.modelData
                        ? viewportCell.modelData.viewportType
                        : ""
                readonly property bool isActive:
                    viewportCell.modelData
                    === viewportLayout.viewportController
                readonly property var placement:
                    viewportLayout.placementFor(
                        viewportCell.modelData.viewportId,
                        viewportCell.viewportType
                    )

                visible: viewportCell.placement.visible
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.row: viewportCell.placement.row
                Layout.column: viewportCell.placement.column
                Layout.rowSpan: viewportCell.placement.rowSpan
                Layout.columnSpan: viewportCell.placement.columnSpan

                Rectangle {
                    id: viewportSurface

                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    anchors.right: sliceSlider.visible
                        ? sliceSlider.left
                        : parent.right
                    anchors.rightMargin: sliceSlider.visible ? 2 : 0

                    color: Theme.canvasBackground
                    border.width: 1
                    border.color: viewportCell.isActive
                        ? Theme.borderStrong
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

                        onDoubleTapped: {
                            viewportLayout.toggleSingleView(
                                viewportCell.modelData.viewportId
                            )
                        }
                    }
                }

                // Slider 位于视口边框之外，单独占用右侧布局空间。
                SliceSlider {
                    id: sliceSlider

                    anchors.top: parent.top
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    z: 20

                    viewportController: viewportCell.modelData
                }
            }
        }
    }
}
