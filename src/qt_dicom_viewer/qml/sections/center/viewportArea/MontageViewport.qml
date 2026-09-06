pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../../components" as Components
import "../../../theme"

Item {
    id: montageRoot

    required property var viewportController
    readonly property var metadataItems: [
        {
            "label": "患者姓名",
            "value": montageRoot.viewportController.patientName
        },
        {
            "label": "患者 ID / 性别 / 年龄",
            "value": montageRoot.viewportController.patientSummary
        },
        {
            "label": "检查 / 序列描述",
            "value": montageRoot.viewportController.descriptionSummary
        },
        {
            "label": "扫描参数",
            "value": montageRoot.viewportController.scanParameters
        },
        {
            "label": "采集日期 / 时间",
            "value": montageRoot.viewportController.acquisitionDateTime
        },
        {
            "label": "层厚",
            "value": montageRoot.viewportController.sliceThickness
        }
    ]

    function formatNumber(value) {
        if (!Number.isFinite(value))
            return "—"
        const rounded = Math.round(value * 100) / 100
        return String(rounded)
    }

    function setColumnCount(count) {
        const oldColumns = Math.max(1, montageRoot.viewportController.columnCount)
        const oldRow = Math.max(0, Math.floor(montageGrid.contentY / montageGrid.cellHeight))
        const anchorIndex = Math.min(
            montageRoot.viewportController.sliceCount - 1,
            oldRow * oldColumns
        )
        montageRoot.viewportController.setColumnCount(count)
        Qt.callLater(function() {
            if (anchorIndex >= 0)
                montageGrid.positionViewAtIndex(anchorIndex, GridView.Beginning)
            montageGrid.updateVisibleRange()
        })
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 158
            color: Theme.panelBackgroundSoft

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 10

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Text {
                            text: "序列平铺"
                            color: Theme.textPrimary
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                        }

                        Text {
                            Layout.fillWidth: true
                            text: montageRoot.viewportController.sliceCount
                                + " 张切片 · WW "
                                + (montageRoot.viewportController.hasWindow
                                    ? montageRoot.formatNumber(
                                        montageRoot.viewportController.windowWidth
                                    ) : "—")
                                + " / WL "
                                + (montageRoot.viewportController.hasWindow
                                    ? montageRoot.formatNumber(
                                        montageRoot.viewportController.windowCenter
                                    ) : "—")
                                + " · "
                                + (montageRoot.viewportController.modality || "—")
                            color: Theme.textMuted
                            font.pixelSize: 11
                            elide: Text.ElideRight
                        }
                    }

                    Repeater {
                        model: [2, 3, 4, 5, 6]

                        delegate: Components.AppButton {
                            required property int modelData

                            compact: true
                            minimumButtonWidth: 38
                            text: String(modelData)
                            checked: modelData
                                === montageRoot.viewportController.columnCount
                            onClicked: montageRoot.setColumnCount(modelData)
                        }
                    }
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 3
                    columnSpacing: 24
                    rowSpacing: 8

                    Repeater {
                        model: montageRoot.metadataItems

                        delegate: ColumnLayout {
                            required property var modelData

                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            spacing: 2

                            Text {
                                Layout.fillWidth: true
                                text: parent.modelData.label
                                color: Theme.textSubtle
                                font.pixelSize: 9
                                elide: Text.ElideRight
                            }

                            Text {
                                Layout.fillWidth: true
                                text: parent.modelData.value || "—"
                                color: Theme.textSecondary
                                font.pixelSize: 11
                                elide: Text.ElideRight
                            }
                        }
                    }
                }
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: Theme.dividerColor
            }
        }

        Rectangle {
            id: gridViewport

            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            color: Theme.workspaceBackground

            GridView {
                id: montageGrid
                objectName: "montageGrid"

                anchors.fill: parent
                clip: true
                interactive: false
                boundsBehavior: Flickable.StopAtBounds
                model: montageRoot.viewportController.sliceModel
                readonly property real gutter: 8
                cellWidth: width / Math.max(
                    1,
                    montageRoot.viewportController.columnCount
                )
                cellHeight: Math.max(
                    96,
                    (cellWidth - gutter)
                        / montageRoot.viewportController.imageAspectRatio
                        + gutter
                )

                function updateVisibleRange() {
                    if (count <= 0 || cellHeight <= 0 || height <= 0)
                        return
                    const columns = montageRoot.viewportController.columnCount
                    const firstRow = Math.max(
                        0,
                        Math.floor(contentY / cellHeight)
                    )
                    const lastRow = Math.max(
                        firstRow,
                        Math.floor((contentY + height - 1) / cellHeight)
                    )
                    const first = Math.min(count - 1, firstRow * columns)
                    const last = Math.min(
                        count - 1,
                        (lastRow + 1) * columns - 1
                    )
                    montageRoot.viewportController.setVisibleRange(first, last)
                }

                onContentYChanged: updateVisibleRange()
                onHeightChanged: Qt.callLater(updateVisibleRange)
                onWidthChanged: Qt.callLater(updateVisibleRange)
                onCellHeightChanged: Qt.callLater(updateVisibleRange)
                onCountChanged: Qt.callLater(updateVisibleRange)
                Component.onCompleted: Qt.callLater(updateVisibleRange)

                Basic.ScrollBar.vertical: Basic.ScrollBar {
                    policy: Basic.ScrollBar.AlwaysOn
                }

                delegate: Rectangle {
                id: tile

                required property int sliceIndex
                required property string imageSource
                required property string loadState
                required property string errorText

                width: montageGrid.cellWidth - montageGrid.gutter
                height: montageGrid.cellHeight - montageGrid.gutter
                x: montageGrid.gutter / 2
                y: montageGrid.gutter / 2
                clip: true
                color: Theme.canvasBackground
                border.width: tileHover.hovered ? 1 : 0
                border.color: Theme.selectionBorder
                radius: 4

                Item {
                    id: imageScene

                    width: parent.width
                    height: parent.height
                    x: montageRoot.viewportController.panX * parent.width
                    y: montageRoot.viewportController.panY * parent.height
                    transformOrigin: Item.Center
                    scale: montageRoot.viewportController.zoom
                    rotation: montageRoot.viewportController.rotationDegrees

                    Item {
                        id: flipLayer
                        anchors.fill: parent

                        transform: Scale {
                            origin.x: flipLayer.width / 2
                            origin.y: flipLayer.height / 2
                            xScale: montageRoot.viewportController.horizontalFlip
                                ? -1 : 1
                            yScale: montageRoot.viewportController.verticalFlip
                                ? -1 : 1
                        }

                        Image {
                            anchors.fill: parent
                            source: tile.imageSource
                            fillMode: Image.PreserveAspectFit
                            cache: false
                            smooth: true
                        }
                    }
                }

                Basic.BusyIndicator {
                    anchors.centerIn: parent
                    running: tile.loadState === "loading"
                    visible: running
                    width: 28
                    height: 28
                }

                Column {
                    anchors.centerIn: parent
                    spacing: 8
                    visible: tile.loadState === "error"

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: Math.min(180, tile.width - 24)
                        text: tile.errorText || "切片加载失败"
                        color: Theme.dangerColor
                        font.pixelSize: 10
                        horizontalAlignment: Text.AlignHCenter
                        elide: Text.ElideRight
                    }

                    Basic.Button {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "重试"
                        onClicked: montageRoot.viewportController.retrySlice(
                            tile.sliceIndex
                        )
                    }
                }

                Rectangle {
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.margins: 7
                    width: sliceLabel.implicitWidth + 12
                    height: 23
                    radius: 5
                    color: "#b0000000"

                    Text {
                        id: sliceLabel
                        anchors.centerIn: parent
                        text: (tile.sliceIndex + 1) + " / "
                            + montageRoot.viewportController.sliceCount
                        color: Theme.overlayText
                        font.pixelSize: 10
                        font.weight: Font.DemiBold
                    }
                }

                HoverHandler {
                    id: tileHover
                    cursorShape: montageRoot.viewportController.activeInteraction
                        === "pan" ? Qt.SizeAllCursor
                        : montageRoot.viewportController.activeInteraction
                            === "zoom" ? Qt.SizeVerCursor
                            : Qt.CrossCursor
                }

                TapHandler {
                    acceptedButtons: Qt.LeftButton
                    onTapped: montageRoot.viewportController.openSlice(
                        tile.sliceIndex
                    )
                }

                DragHandler {
                    id: tileDrag
                    target: null
                    acceptedButtons: Qt.LeftButton
                        | Qt.RightButton
                        | Qt.MiddleButton
                    property point lastPosition: Qt.point(0, 0)

                    onActiveChanged: {
                        if (active) {
                            lastPosition = centroid.position
                            montageRoot.viewportController.beginInteraction(
                                centroid.pressPosition.x,
                                centroid.pressPosition.y,
                                centroid.pressedButtons,
                                tile.width,
                                tile.height
                            )
                        } else {
                            montageRoot.viewportController.endInteraction(
                                centroid.position.x,
                                centroid.position.y
                            )
                        }
                    }

                    onActiveTranslationChanged: {
                        if (!active)
                            return
                        const current = centroid.position
                        const step = Qt.point(
                            current.x - lastPosition.x,
                            current.y - lastPosition.y
                        )
                        montageRoot.viewportController.updateInteraction(
                            centroid.pressPosition,
                            current,
                            step,
                            activeTranslation
                        )
                        lastPosition = current
                    }
                }
            }
            }

            MouseArea {
                id: wheelArea
                objectName: "montageWheelArea"

                anchors.fill: parent
                z: 100
                acceptedButtons: Qt.NoButton
                hoverEnabled: false
                scrollGestureEnabled: true

                onWheel: wheelEvent => {
                    const pixelStep = wheelEvent.pixelDelta.y !== 0
                        ? wheelEvent.pixelDelta.y
                        : wheelEvent.angleDelta.y / 120
                            * montageGrid.cellHeight * 0.65
                    const maximum = Math.max(
                        0,
                        montageGrid.contentHeight - montageGrid.height
                    )
                    montageGrid.contentY = Math.max(
                        0,
                        Math.min(maximum, montageGrid.contentY - pixelStep)
                    )
                    wheelEvent.accepted = true
                }
            }
        }
    }
}
