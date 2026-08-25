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
    readonly property var activeViewport: workspaceController.activeViewports.length > 0 ? workspaceController.activeViewports[0] : null
    readonly property var toolController: workspaceController.activeTab ? workspaceController.activeTab.toolController : null

    width: 1200
    height: 760
    visible: true
    title: "Qt DICOM Viewer"
    color: Theme.appBackground

    RowLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        Sections.LeftPanel {
            Layout.preferredWidth: 250
            Layout.fillHeight: true
            panelController: window.panelController
        }

        CenterSections.CenterPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            workspaceController: window.workspaceController
            panelController: window.panelController
            activeViewport: window.activeViewport
        }

        Sections.RightPanel {
            visible: window.hasTabs
            Layout.preferredWidth: visible ? 260 : 0
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
