pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../components" as Components

Rectangle {
    id: rightPanel

    property int currentToolIndex: 0

    readonly property var primaryTools: [
        { "iconName": "window", "label": "调窗" },
        { "iconName": "scroll", "label": "翻页" },
        { "iconName": "pan", "label": "平移" },
        { "iconName": "zoom", "label": "缩放" },
        { "iconName": "measure", "label": "测量" },
        { "iconName": "annotate", "label": "标注" },
        { "iconName": "reset", "label": "重置" }
    ]

    color: "#1b1f26"
    border.color: "#303744"
    border.width: 1
    radius: 8
    clip: true

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: toolFlow.height + 16
            color: "#1d222a"

            Flow {
                id: toolFlow

                readonly property real availableWidth: parent.width - 16
                readonly property real buttonMinWidth: 36
                readonly property real buttonMaxWidth: 46
                readonly property real buttonHeight: 44
                readonly property int maxColumnsByWidth: Math.max(
                    1,
                    Math.floor(
                        (toolFlow.availableWidth + toolFlow.spacing)
                        / (toolFlow.buttonMinWidth + toolFlow.spacing)
                    )
                )
                readonly property int preferredTwoRowColumns: Math.ceil(
                    rightPanel.primaryTools.length / 2
                )
                readonly property int columns: {
                    if (toolFlow.maxColumnsByWidth
                            >= rightPanel.primaryTools.length) {
                        return rightPanel.primaryTools.length
                    }

                    if (toolFlow.maxColumnsByWidth
                            >= toolFlow.preferredTwoRowColumns) {
                        return toolFlow.preferredTwoRowColumns
                    }

                    return toolFlow.maxColumnsByWidth
                }
                readonly property int rows: Math.ceil(
                    rightPanel.primaryTools.length / toolFlow.columns
                )
                readonly property real buttonWidth: Math.min(
                    toolFlow.buttonMaxWidth,
                    Math.max(
                        toolFlow.buttonMinWidth,
                        (toolFlow.availableWidth
                            - (toolFlow.columns - 1) * toolFlow.spacing)
                            / toolFlow.columns
                    )
                )

                anchors.top: parent.top
                anchors.topMargin: 8
                anchors.horizontalCenter: parent.horizontalCenter
                width: toolFlow.columns * toolFlow.buttonWidth
                    + (toolFlow.columns - 1) * toolFlow.spacing
                height: toolFlow.rows * toolFlow.buttonHeight
                    + (toolFlow.rows - 1) * toolFlow.spacing
                spacing: 6

                Repeater {
                    model: rightPanel.primaryTools

                    delegate: Basic.Button {
                        id: primaryButton

                        required property int index
                        required property var modelData

                        width: toolFlow.buttonWidth
                        height: toolFlow.buttonHeight
                        checked: primaryButton.index === rightPanel.currentToolIndex

                        onClicked: {
                            rightPanel.currentToolIndex = primaryButton.index
                        }

                        Basic.ToolTip.visible: primaryButton.hovered
                        Basic.ToolTip.delay: 400
                        Basic.ToolTip.text: primaryButton.modelData.label

                        contentItem: Item {
                            Components.AppIcon {
                                anchors.centerIn: parent
                                iconName: primaryButton.modelData.iconName
                                iconSize: 22
                                iconColor: primaryButton.checked
                                    ? "#65b5e8"
                                    : primaryButton.hovered ? "#d7e0e8" : "#8e9aa8"
                            }
                        }

                        background: Rectangle {
                            color: primaryButton.checked
                                ? "#253b4b"
                                : primaryButton.hovered ? "#252c35" : "transparent"
                            border.color: primaryButton.checked ? "#3d7599" : "transparent"
                            border.width: 1
                            radius: 6
                        }
                    }
                }
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: "#303744"
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }
}
