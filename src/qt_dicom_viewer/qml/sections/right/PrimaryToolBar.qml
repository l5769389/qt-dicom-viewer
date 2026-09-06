pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import "../../components" as Components
import "../../theme"

Rectangle {
    id: toolBar

    required property var toolController
    property var viewportController: null
    readonly property var volumeController: viewportController && viewportController.viewportType === "volume"
        ? viewportController : null
    property bool playbackActive: false

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
        // Integral widths prevent floating-point overflow from wrapping the last
        // button into an extra row outside the toolbar's calculated height.
        readonly property real buttonWidth: Math.floor(Math.min(toolFlow.buttonMaxWidth, Math.max(toolFlow.buttonMinWidth, (toolFlow.availableWidth - (toolFlow.columns - 1) * toolFlow.spacing) / toolFlow.columns)))

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
                objectName: "primaryTool-" + primaryButton.modelData.toolType
                readonly property bool feedbackActive: primaryButton.modelData.toolType === toolBar.feedbackTool
                readonly property bool bedAction: primaryButton.modelData.toolType === "volume-bed"
                readonly property bool toolActive: bedAction
                    ? !!toolBar.volumeController && toolBar.volumeController.bedRemovalEnabled
                    : toolBar.toolController ? primaryButton.modelData.toolType === toolBar.toolController.activeTool : false
                readonly property bool resetAction:
                    primaryButton.modelData.toolType === "reset"
                readonly property bool directionAction:
                    primaryButton.modelData.toolType === "volume-direction"

                width: toolFlow.buttonWidth
                height: toolFlow.buttonHeight
                enabled: (!toolBar.playbackActive || primaryButton.modelData.toolType === "play")
                    && (!bedAction || (toolBar.volumeController
                        && toolBar.volumeController.bedRemovalAvailable && !toolBar.volumeController.editBusy))
                opacity: enabled ? 1 : 0.38
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
                Basic.ToolTip.text: primaryButton.bedAction
                    ? "去床板（CT） · " + (primaryButton.toolActive ? "已启用，点击关闭" : "点击启用")
                    : primaryButton.modelData.label + (primaryButton.directionAction
                    && toolBar.volumeController ? " · " + toolBar.volumeController.currentFace : "")
                Accessible.name: primaryButton.modelData.label
                Accessible.checkable: primaryButton.bedAction
                Accessible.checked: primaryButton.bedAction && primaryButton.toolActive

                contentItem: Item {
                    Components.AppIcon {
                        visible: !primaryButton.directionAction
                        anchors.centerIn: parent
                        iconName: primaryButton.modelData.iconName
                        iconSize: 22
                        iconColor: !primaryButton.enabled
                            ? Theme.textDisabled
                            : primaryButton.resetAction
                            ? Theme.resetActionColor
                            : primaryButton.checked
                            ? Theme.iconActive
                            : primaryButton.hovered
                                ? Theme.iconHover
                                : Theme.iconDefault
                    }
                    Rectangle {
                        visible: primaryButton.directionAction
                        anchors.centerIn: parent
                        width: 26
                        height: 26
                        radius: 4
                        color: toolBar.volumeController ? toolBar.volumeController.currentFaceColor : Theme.iconDefault
                        Text {
                            objectName: "currentVolumeFace"
                            anchors.centerIn: parent
                            text: toolBar.volumeController ? toolBar.volumeController.currentFace : "A"
                            color: "white"
                            font.pixelSize: 17
                            font.bold: true
                        }
                    }
                }

                background: Rectangle {
                    color: primaryButton.resetAction
                        ? primaryButton.down
                            ? Theme.resetActionPressed
                            : primaryButton.hovered
                                ? Theme.resetActionHover
                                : Theme.resetActionSurface
                        : primaryButton.checked
                        ? Theme.selectionBackground
                        : primaryButton.hovered
                            ? Theme.controlHover
                            : "transparent"
                    border.color: primaryButton.resetAction
                        ? "transparent"
                        : primaryButton.checked
                        ? Theme.selectionBorder
                        : "transparent"
                    border.width: !primaryButton.resetAction
                        && primaryButton.checked ? 1 : 0
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
