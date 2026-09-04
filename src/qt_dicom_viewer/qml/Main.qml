import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "sections" as Sections
import "sections/center" as CenterSections
import "theme"

ApplicationWindow {
    id: window
    readonly property var panelController: appController.panelController
    readonly property var workspaceController: appController.workspaceController
    readonly property bool hasTabs: workspaceController.tabs.length > 0
    readonly property var viewportController:
        workspaceController.activeViewport
    readonly property var currentTabAllViewports: workspaceController.currentTabAllViewports
    readonly property var toolController: workspaceController.activeTab ? workspaceController.activeTab.toolController : null

    width: 1400
    height: 760
    minimumWidth: 1000
    minimumHeight: 600
    visible: true
    title: "Qt DICOM Viewer"
    color: Theme.appBackground

    RowLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        Sections.LeftPanel {
            Layout.minimumWidth: 210
            Layout.preferredWidth: 240
            Layout.maximumWidth: 280
            Layout.fillHeight: true
            panelController: window.panelController
        }

        CenterSections.CenterPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            workspaceController: window.workspaceController
            panelController: window.panelController
            currentTabAllViewports: window.currentTabAllViewports
            viewportController: window.viewportController
        }

        Sections.RightPanel {
            visible: window.hasTabs
            Layout.minimumWidth: visible ? 220 : 0
            Layout.preferredWidth: visible ? 250 : 0
            Layout.maximumWidth: visible ? 280 : 0
            Layout.fillHeight: true
            toolController: window.toolController
            viewportController: window.viewportController
            tabController: window.workspaceController.activeTab
            toolVisible: window.hasTabs
            // onRotationActionTriggered: action => {
            //     if (window.viewportController) {
            //         window.viewportController.applyTransformAction(action)
            //     }
            // }

        }
    }
}
