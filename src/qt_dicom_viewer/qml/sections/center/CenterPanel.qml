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

        Loader {
            Layout.fillWidth: true
            Layout.fillHeight: true
            active: centerPanel.hasTabs
            sourceComponent: centerPanel.workspaceController.activeTabType === "3d"
                ? volumeComponent : imageComponent
        }
    }

    Component {
        id: imageComponent
        ViewportSection.ViewportLayout {
            viewportController: centerPanel.workspaceController.activeTabType === "3d"
                ? null : centerPanel.viewportController
            hasTabs: centerPanel.hasTabs
            tabType: centerPanel.workspaceController.activeTabType
            currentTabAllViewports: centerPanel.workspaceController.activeTabType === "3d"
                ? [] : centerPanel.currentTabAllViewports
            onViewportActivated: viewportId => {
                const activeTab = centerPanel.workspaceController.activeTab
                if (activeTab) {
                    activeTab.activateViewport(viewportId)
                }
            }
        }
    }

    Component {
        id: volumeComponent
        ViewportSection.VolumeViewport {
            viewportController: centerPanel.viewportController
        }
    }

    WorkspaceEmptyState {
        anchors.fill: parent
        visible: !centerPanel.hasTabs
        panelController: centerPanel.panelController
    }
}
