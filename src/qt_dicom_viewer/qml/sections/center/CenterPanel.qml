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
    radius: 8
    clip: true

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        visible: centerPanel.hasTabs

        TabBarSection {
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            // 标签栏与诊断视口属于不同层级，保留明确的背景间隔，
            // 避免两个 active 状态在交界处拼成同一条边框。
            Layout.bottomMargin: 10
            workspaceController: centerPanel.workspaceController
        }

        Loader {
            Layout.fillWidth: true
            Layout.fillHeight: true
            active: centerPanel.hasTabs
            sourceComponent: centerPanel.workspaceController.activeTabType === "tag"
                ? tagComponent
                : centerPanel.workspaceController.activeTabType === "3d"
                    ? volumeComponent
                    : centerPanel.workspaceController.activeTabType === "montage"
                        ? montageComponent : imageComponent
        }
    }

    Component {
        id: tagComponent
        TagPanel {
            tagController: centerPanel.workspaceController.activeTab
                ? centerPanel.workspaceController.activeTab.tagController
                : null
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

    Component {
        id: montageComponent
        ViewportSection.MontageViewport {
            viewportController: centerPanel.viewportController
        }
    }

    WorkspaceEmptyState {
        anchors.fill: parent
        visible: !centerPanel.hasTabs
        panelController: centerPanel.panelController
    }
}
