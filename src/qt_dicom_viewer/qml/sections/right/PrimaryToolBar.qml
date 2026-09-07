pragma ComponentBehavior: Bound

import QtQuick
import "../../components" as Components
import "../../theme"

Rectangle {
    id: toolBar
    required property var toolController
    property var viewportController: null
    readonly property var volumeController: viewportController && viewportController.viewportType === "volume"
        ? viewportController : null
    property bool playbackActive: false
    readonly property var tools: toolController ? toolController.tools : []
    property string feedbackTool: ""
    signal toolTriggered(var toolDefinition)

    implicitHeight: toolFlow.childrenRect.height + 12
    color: Theme.panelBackgroundStrong
    radius: Theme.controlRadius

    Timer {
        id: feedbackTimer
        interval: 180
        onTriggered: toolBar.feedbackTool = ""
    }

    Flow {
        id: toolFlow
        readonly property real availableWidth: Math.max(0, toolBar.width - 12)
        readonly property int columns: Math.max(1, Math.min(5,
            Math.floor((availableWidth + spacing) / (44 + spacing))))
        readonly property int rows: Math.ceil(toolBar.tools.length / columns)
        readonly property real buttonWidth: Math.max(0,
            (availableWidth - (columns - 1) * spacing) / columns)
        anchors.top: parent.top
        anchors.topMargin: 6
        anchors.horizontalCenter: parent.horizontalCenter
        width: availableWidth
        height: rows * Theme.toolbarButtonHeight + Math.max(0, rows - 1) * spacing
        spacing: 4

        Repeater {
            model: toolBar.tools
            delegate: Components.ToolbarAction {
                id: primaryAction
                required property var modelData
                readonly property bool bedAction: modelData.toolType === "volume-bed"
                width: toolFlow.buttonWidth
                height: Theme.toolbarButtonHeight
                buttonObjectName: "primaryTool-" + modelData.toolType
                label: modelData.label
                shortLabel: modelData.toolType === "mpr-rotate-3d" ? "3D旋转" : label
                iconName: modelData.iconName
                placeholder: modelData.available === false
                actionEnabled: (!toolBar.playbackActive || modelData.toolType === "play")
                    && (!bedAction || (toolBar.volumeController
                        && toolBar.volumeController.bedRemovalAvailable && !toolBar.volumeController.editBusy))
                checked: bedAction ? !!toolBar.volumeController && toolBar.volumeController.bedRemovalEnabled
                    : modelData.toolType === toolBar.feedbackTool
                    || (toolBar.toolController && modelData.toolType === toolBar.toolController.activeTool)
                resetAction: modelData.toolType === "reset"
                directionFace: modelData.toolType === "volume-direction"
                    ? (toolBar.volumeController ? toolBar.volumeController.currentFace : "A") : ""
                directionColor: toolBar.volumeController
                    ? toolBar.volumeController.currentFaceColor : Theme.iconDefault
                tooltipText: label + (placeholder ? " · 待实现"
                    : !actionEnabled ? (toolBar.playbackActive ? " · 播放期间不可用" : toolBar.volumeController && toolBar.volumeController.editBusy ? " · 正在处理体数据" : " · 当前体数据不支持")
                    : directionFace !== "" ? " · " + directionFace : "")
                onTriggered: {
                    if (modelData.behavior === "command") {
                        toolBar.feedbackTool = modelData.toolType
                        feedbackTimer.restart()
                    }
                    toolBar.toolTriggered(modelData)
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
