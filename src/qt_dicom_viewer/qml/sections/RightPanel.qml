pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "right" as Right

Rectangle {
    id: rightPanel

    required property var toolController
    required property bool toolVisible
    required property var activeViewport

    color: "#1b1f26"
    border.color: "#303744"
    border.width: 1
    radius: 8
    clip: true

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        visible: rightPanel.toolVisible

        Right.PrimaryToolBar {
            Layout.fillWidth: true
            Layout.preferredHeight: implicitHeight
            toolController: rightPanel.toolController

            onToolTriggered: toolDefinition => {
                rightPanel.toolController?.activateTool(
                    toolDefinition.toolType
                )
            }
        }

        Right.ToolDetailPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            toolController: rightPanel.toolController
            activePanel: rightPanel.toolController ? rightPanel.toolController.activePanel : ""
            activeViewport: rightPanel.activeViewport
        }
    }
}
