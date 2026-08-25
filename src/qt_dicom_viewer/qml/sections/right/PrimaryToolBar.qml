pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import "../../components" as Components
import "../../theme"

Rectangle {
    id: toolBar

    required property var toolController

    readonly property var tools: toolBar.toolController
        ? toolBar.toolController.tools
        : []

    signal toolTriggered(var toolDefinition)

    implicitHeight: toolFlow.height + 16
    color: Theme.panelBackgroundStrong
    property string feedbackTool: ""

    Timer {
        id: feedbackTimer

        interval: 180
        repeat: false

        onTriggered: {
            toolBar.feedbackTool = ""
        }
    }
    Flow {
        id: toolFlow

        readonly property real availableWidth: toolBar.width - 16
        readonly property real buttonMinWidth: 36
        readonly property real buttonMaxWidth: 46
        readonly property real buttonHeight: 44
        readonly property int maxColumnsByWidth: Math.max(1, Math.floor((toolFlow.availableWidth + toolFlow.spacing) / (toolFlow.buttonMinWidth + toolFlow.spacing)))
        readonly property int preferredTwoRowColumns: Math.ceil(toolBar.tools.length / 2)
        readonly property int columns: {
            if (toolFlow.maxColumnsByWidth >= toolBar.tools.length) return toolBar.tools.length

            if (toolFlow.maxColumnsByWidth >= toolFlow.preferredTwoRowColumns) return toolFlow.preferredTwoRowColumns

            return toolFlow.maxColumnsByWidth
        }
        readonly property int rows: Math.ceil(toolBar.tools.length / toolFlow.columns)
        readonly property real buttonWidth: Math.min(toolFlow.buttonMaxWidth, Math.max(toolFlow.buttonMinWidth, (toolFlow.availableWidth - (toolFlow.columns - 1) * toolFlow.spacing) / toolFlow.columns))

        anchors.top: parent.top
        anchors.topMargin: 8
        anchors.horizontalCenter: parent.horizontalCenter
        width: toolFlow.columns * toolFlow.buttonWidth + (toolFlow.columns - 1) * toolFlow.spacing
        height: toolFlow.rows * toolFlow.buttonHeight + (toolFlow.rows - 1) * toolFlow.spacing
        spacing: 6

        Repeater {
            model: toolBar.tools

            delegate: Basic.Button
            {
                id: primaryButton

                required property var modelData
                readonly property bool feedbackActive: primaryButton.modelData.toolType === toolBar.feedbackTool
                readonly property bool toolActive: toolBar.toolController ? primaryButton.modelData.toolType === toolBar.toolController.activeTool : false

                width: toolFlow.buttonWidth
                height: toolFlow.buttonHeight
                checked: primaryButton.toolActive || primaryButton.feedbackActive

                onClicked: {
                    if (modelData.behavior === "command") {
                        toolBar.feedbackTool = modelData.toolType
                        feedbackTimer.restart()
                    }
                    toolBar.toolTriggered(modelData)
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
                            ? Theme.iconActive
                            : primaryButton.hovered
                                ? Theme.iconHover
                                : Theme.iconDefault
                    }
                }

                background: Rectangle {
                    color: primaryButton.checked
                        ? Theme.selectionBackground
                        : primaryButton.hovered
                            ? Theme.controlHover
                            : "transparent"
                    border.color: primaryButton.checked
                        ? Theme.selectionBorder
                        : "transparent"
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
        color: Theme.dividerColor
    }
}
