pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "right" as Right
import "../theme"

Rectangle {
    id: rightPanel
    objectName: "rightPanel"

    required property var toolController
    required property bool toolVisible
    required property var viewportController
    property var tabController: null

    color: Theme.panelBackground
    border.color: Theme.borderDefault
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
            viewportController: rightPanel.viewportController
            playbackActive: rightPanel.tabController
                ? rightPanel.tabController.playing
                : false

            onToolTriggered: toolDefinition => {
                rightPanel.toolController?.activateTool(
                    toolDefinition.toolType
                )
            }
        }

        Flickable {
            id: detailFlickable
            objectName: "toolDetailFlickable"

            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: width
            contentHeight: Math.max(
                height,
                toolDetailPanel.implicitHeight
            )
            boundsBehavior: Flickable.StopAtBounds

            Right.ToolDetailPanel {
                id: toolDetailPanel

                width: detailFlickable.width
                height: detailFlickable.contentHeight
                toolController: rightPanel.toolController
                activePanel: rightPanel.toolController
                    ? rightPanel.toolController.activePanel
                    : ""
                viewportController: rightPanel.viewportController
                tabController: rightPanel.tabController
            }

            Basic.ScrollBar.vertical: Basic.ScrollBar {
                policy: detailFlickable.contentHeight
                    > detailFlickable.height
                    ? Basic.ScrollBar.AsNeeded
                    : Basic.ScrollBar.AlwaysOff
            }
        }

        Right.ToolResetBar {
            Layout.fillWidth: true
            toolController: rightPanel.toolController
        }
    }
}
