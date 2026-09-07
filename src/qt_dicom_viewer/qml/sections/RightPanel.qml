pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "right" as Right
import "../theme"
import "../components" as Components

Rectangle {
    id: rightPanel
    objectName: "rightPanel"

    required property var toolController
    required property bool toolVisible
    required property var viewportController
    property var tabController: null
    property var exportController: null
    property Item exportItem: null
    signal manualRequested(string chapter)
    readonly property var volumeController: viewportController && viewportController.viewportType === "volume"
        ? viewportController : null

    color: Theme.panelBackground
    border.color: Theme.borderDefault
    border.width: 1
    radius: 8
    clip: true

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 1
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

        Text {
            objectName: "volumeEditStatus"
            Layout.fillWidth: true
            Layout.margins: visible ? 10 : 0
            visible: !!rightPanel.volumeController && (rightPanel.volumeController.bedRemovalEnabled
                || rightPanel.volumeController.editMessage !== "")
            text: rightPanel.volumeController
                ? [rightPanel.volumeController.bedRemovalEnabled ? "去床板已启用" : "",
                    rightPanel.volumeController.editMessage].filter(s => s !== "").join("\n") : ""
            color: Theme.textSecondary
            font.pixelSize: 12
            wrapMode: Text.Wrap
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

                width: detailFlickable.width - (detailFlickable.contentHeight > detailFlickable.height ? 10 : 0)
                height: detailFlickable.contentHeight
                toolController: rightPanel.toolController
                activePanel: rightPanel.toolController
                    ? rightPanel.toolController.activePanel
                    : ""
                viewportController: rightPanel.viewportController
                tabController: rightPanel.tabController
                exportController: rightPanel.exportController
                exportItem: rightPanel.exportItem
                onManualRequested: chapter => rightPanel.manualRequested(chapter)
            }

            Basic.ScrollBar.vertical: Components.AppScrollBar {
                policy: detailFlickable.contentHeight
                    > detailFlickable.height
                    ? Basic.ScrollBar.AsNeeded
                    : Basic.ScrollBar.AlwaysOff
            }
        }

        Right.ToolResetBar {
            Layout.fillWidth: true
            toolController: rightPanel.toolController
            voiController: rightPanel.tabController?.voiController ?? rightPanel.viewportController?.voiController ?? null
        }
    }

}
