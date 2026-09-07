pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import 'viewportArea' as ViewportSection
import "../../theme"
import "../settings" as Settings
import "../pacs" as Pacs

Rectangle {
    id: centerPanel

    required property var workspaceController
    required property var panelController
    property var pacsController: null
    property var settingsController: null
    required property var viewportController
    required property var currentTabAllViewports

    readonly property bool imageWorkspace: ["2d", "mpr", "4d", "petctfusion"].includes(workspaceController.activeTabType)

    readonly property Item exportItem: workspaceLoader.item
        ? (workspaceLoader.item.activeExportItem !== undefined ? workspaceLoader.item.activeExportItem() : workspaceLoader.item) : null

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
            id: workspaceLoader
            Layout.fillWidth: true
            Layout.fillHeight: true
            active: centerPanel.hasTabs
            sourceComponent: centerPanel.workspaceController.activeTabType === "settings"
                ? settingsComponent
                : centerPanel.workspaceController.activeTabType === "pacs"
                ? pacsComponent
                : centerPanel.workspaceController.activeTabType === "tag"
                ? tagComponent
                : centerPanel.workspaceController.activeTabType === "3d"
                    ? volumeComponent
                    : centerPanel.workspaceController.activeTabType === "montage"
                        ? montageComponent : imageComponent
        }
    }

    Component {
        id: settingsComponent
        Settings.SettingsPage { pacsController: centerPanel.pacsController; settingsController: centerPanel.settingsController }
    }

    Component {
        id: pacsComponent
        Pacs.PacsBrowser { pacsController: centerPanel.pacsController; workspaceController: centerPanel.workspaceController }
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
            viewportController: centerPanel.imageWorkspace ? centerPanel.viewportController : null
            hasTabs: centerPanel.hasTabs
            tabType: centerPanel.workspaceController.activeTabType
            currentTabAllViewports: centerPanel.imageWorkspace ? centerPanel.currentTabAllViewports : []
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
            viewportController: centerPanel.workspaceController.activeTab?.activeViewport ?? null
        }
    }

    WorkspaceEmptyState {
        anchors.fill: parent
        visible: !centerPanel.hasTabs
        panelController: centerPanel.panelController
        pacsController: centerPanel.pacsController
        workspaceController: centerPanel.workspaceController
    }
}
