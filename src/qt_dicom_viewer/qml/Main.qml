import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "sections" as Sections
import "sections/center" as CenterSections

ApplicationWindow {
    id: window
    readonly property var workspaceController: appController.workspaceController
    readonly property bool hasTabs: workspaceController.tabs.length > 0
    readonly property var activeViewport: workspaceController.activeViewports.length > 0 ? workspaceController.activeViewports[0] : null
    readonly property var toolController: workspaceController.activeTab ? workspaceController.activeTab.toolController : null

    width: 1200
    height: 760
    visible: true
    title: "Qt DICOM Viewer"
    color: "#111419"

    RowLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        Sections.LeftPanel {
            Layout.preferredWidth: 220
            Layout.fillHeight: true
            panelController: appController.panelController
        }

        CenterSections.CenterPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            workspaceController: window.workspaceController
            activeViewport: window.activeViewport
        }

        Sections.RightPanel {
            Layout.preferredWidth: 260
            Layout.fillHeight: true
            toolController: window.toolController
            activeViewport: window.activeViewport
            toolVisible: window.hasTabs
            // onRotationActionTriggered: action => {
            //     if (window.activeViewport) {
            //         window.activeViewport.applyTransformAction(action)
            //     }
            // }

        }
    }
}
