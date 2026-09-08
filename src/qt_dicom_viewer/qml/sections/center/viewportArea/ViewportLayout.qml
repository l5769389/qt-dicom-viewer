pragma
ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "../../../components" as Components
import "../../../theme"

Item {
    id: viewportLayout

    required property var viewportController
    required property var currentTabAllViewports
    required property string tabType
    required property bool hasTabs
    property string layoutMode: "grid"
    property string focusedViewportId: ""
    readonly property bool petWorkspace: currentTabAllViewports.length === 4
        && currentTabAllViewports.some(v => v.viewportRole === "mip")
    readonly property var petController: petWorkspace ? currentTabAllViewports[0].reconstructionController : null
    readonly property var petPlacements: ({
        "axial": {row: 0, column: 0}, "coronal": {row: 0, column: 1},
        "sagittal": {row: 1, column: 0}, "mip": {row: 1, column: 1},
        "ct": {row: 0, column: 0}, "pet": {row: 0, column: 1},
        "fusion": {row: 1, column: 0}
    })
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

    function activeExportItem() {
        for (let i = 0; i < viewportRepeater.count; i++) {
            const cell = viewportRepeater.itemAt(i)
            if (cell && cell.modelData === viewportController) return cell.exportItem
        }
        return null
    }
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

    function placementFor(viewportId, viewportType, role) {
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

        const placement = viewportLayout.petWorkspace
            ? viewportLayout.petPlacements[role]
            : (viewportLayout.tabType === "mpr" || viewportLayout.tabType === "4d")
            ? viewportLayout.mprPlacements[viewportType]
            : null
        return {
            "visible": true,
            "row": placement ? placement.row : 0,
            "column": placement ? placement.column : 0,
            "rowSpan": placement ? (placement.rowSpan ?? 1) : 1,
            "columnSpan": placement ? (placement.columnSpan ?? 1) : 1
        }
    }

    onCurrentTabAllViewportsChanged: resetLayout()
    onTabTypeChanged: resetLayout()

    RowLayout {
        id: petNavigation
        visible: viewportLayout.petWorkspace
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: visible ? 38 : 0
        spacing: 6
        Repeater {
            model: viewportLayout.petController?.isFusion
                ? [{name:"轴位", value:"axial"}, {name:"冠状位", value:"coronal"}, {name:"矢状位", value:"sagittal"}] : []
            delegate: Components.AppButton {
                required property var modelData
                objectName: "fusionPlane-" + modelData.value
                compact: true
                text: modelData.name
                checkable: true
                checked: viewportLayout.petController?.plane === modelData.value
                onClicked: viewportLayout.petController.setPlane(modelData.value)
            }
        }
        Components.AppButton {
            objectName: "openFusion3D"
            visible: viewportLayout.petController?.isFusion === true
            enabled: viewportLayout.petController?.ready === true
            text: "融合 3D"
            compact: true
            onClicked: viewportLayout.petController.openVolumeView()
        }
        Text {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            text: viewportLayout.petController?.warning ?? ""
            color: Theme.warningColor
            font.pixelSize: 11
            elide: Text.ElideRight
        }
    }

    GridLayout {
        id: viewportGrid

        anchors.fill: parent
        anchors.topMargin: petNavigation.visible ? petNavigation.height + 4 : 0

        columns: ["mpr", "4d"].includes(viewportLayout.tabType) || viewportLayout.petWorkspace ? 2 : 1
        rows: ["mpr", "4d"].includes(viewportLayout.tabType) || viewportLayout.petWorkspace ? 2 : 1
        uniformCellWidths: true
        uniformCellHeights: true

        columnSpacing: 2
        rowSpacing: 2

        Repeater {
            id: viewportRepeater
            model: viewportLayout.currentTabAllViewports

            delegate: Item {
                id: viewportCell
                readonly property alias exportItem: imageViewport

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
                        viewportCell.viewportType,
                        viewportCell.modelData.viewportRole
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

                    Viewport {
                        id: imageViewport
                        anchors.fill: parent
                        anchors.margins: 1
                        anchors.topMargin: 1

                        viewportController: viewportCell.modelData
                        hasTabs: true
                    }
                    // Active viewport 使用两个局部对角角标，不绘制完整边框，
                    // 因而不会在 Tab 下方形成贯穿内容区的横线。
                    Item {
                        anchors.fill: parent
                        visible: viewportCell.isActive
                        z: 30

                        Rectangle {
                            anchors.left: parent.left
                            anchors.top: parent.top
                            width: 18
                            height: 2
                            color: Theme.activeIndicator
                        }

                        Rectangle {
                            anchors.left: parent.left
                            anchors.top: parent.top
                            width: 2
                            height: 18
                            color: Theme.activeIndicator
                        }

                        Rectangle {
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            width: 18
                            height: 2
                            color: Theme.activeIndicator
                        }

                        Rectangle {
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            width: 2
                            height: 18
                            color: Theme.activeIndicator
                        }
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
