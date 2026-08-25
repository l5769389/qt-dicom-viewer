pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import 'viewportArea' as ViewportSection
import "../../theme"

Rectangle {
    id: centerPanel

    required property var workspaceController
    required property var panelController
    required property var viewportController
    required property var currentTabAllViewports

    readonly property bool hasTabs:
        workspaceController.tabs.length > 0

    color: Theme.workspaceBackground
    border.color: Theme.borderDefault
    border.width: 1
    radius: 8
    clip: true

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        visible: centerPanel.hasTabs

        TabBarSection {
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            Layout.bottomMargin: 4
            workspaceController: centerPanel.workspaceController
        }

        ViewportSection.ViewportLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            viewportController: centerPanel.viewportController
            hasTabs: centerPanel.hasTabs
            tabType: centerPanel.workspaceController.activeTabType
            currentTabAllViewports: centerPanel.currentTabAllViewports
            onViewportActivated: viewportId => {
                const activeTab = centerPanel.workspaceController.activeTab
                if (activeTab){
                    activeTab.activateViewport(viewportId)
                }

            }
        }
    }

    WorkspaceEmptyState {
        anchors.fill: parent
        visible: !centerPanel.hasTabs
        panelController: centerPanel.panelController
    }
}
