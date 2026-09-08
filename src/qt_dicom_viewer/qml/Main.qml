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
    readonly property var pacsController: appController.pacsController ?? null
    readonly property var seriesExportController: appController.seriesExportController ?? null
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
    title: "Voxenra"
    color: Theme.appBackground

    RowLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        Sections.SidebarContainer {
            Layout.minimumWidth: implicitWidth
            Layout.preferredWidth: implicitWidth
            Layout.maximumWidth: implicitWidth
            Layout.fillHeight: true
            panelController: window.panelController
            pacsController: window.pacsController
            workspaceController: window.workspaceController
            exportController: window.seriesExportController
        }

        CenterSections.CenterPanel {
            id: centerView
            Layout.fillWidth: true
            Layout.fillHeight: true
            workspaceController: window.workspaceController
            panelController: window.panelController
            pacsController: window.pacsController
            settingsController: appController.settingsController ?? null
            currentTabAllViewports: window.currentTabAllViewports
            viewportController: window.viewportController
        }

        Sections.RightPanel {
            onManualRequested: chapter => window.workspaceController.openManual(chapter)
            exportController: appController.exportController ?? null
            exportItem: centerView.exportItem
            visible: window.hasTabs && ["tag", "settings", "pacs", "manual"].indexOf(window.workspaceController.activeTabType) < 0
            Layout.minimumWidth: visible ? 220 : 0
            Layout.preferredWidth: visible ? 250 : 0
            Layout.maximumWidth: visible ? 280 : 0
            Layout.fillHeight: true
            toolController: window.toolController
            viewportController: window.viewportController
            tabController: visible ? window.workspaceController.activeTab : null
            toolVisible: visible
            // onRotationActionTriggered: action => {
            //     if (window.viewportController) {
            //         window.viewportController.applyTransformAction(action)
            //     }
            // }

        }
    }
    Sections.ExportDialog {
        controller: window.seriesExportController
        settingsController: appController.settingsController ?? null
    }
}
