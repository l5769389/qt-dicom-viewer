pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import 'viewportArea' as ViewportSection
import "../../theme"
import "../settings" as Settings
import "../pacs" as Pacs
import "../manual" as Manual

Rectangle {
    id: centerPanel

    required property var workspaceController
    required property var panelController
    property var pacsController: null
    property var settingsController: null
    required property var viewportController
    required property var currentTabAllViewports

    readonly property var opening: workspaceController.activeLoadState
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

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Loader {
                id: workspaceLoader
                objectName: "workspaceLoader"
                anchors.fill: parent
                asynchronous: true
                active: false
                property var loadedTab: null
                visible: status === Loader.Ready
                function openCurrentTab() {
                    // Cancel the previous incubation before selecting another component.
                    // Binding sourceComponent directly to activeTabType can briefly start
                    // loading the next page during the same active-tab signal delivery.
                    active = false
                    sourceComponent = null
                    Qt.callLater(loadCurrentTab)
                }
                function loadCurrentTab() {
                    if (!centerPanel.hasTabs)
                        return
                    loadedTab = centerPanel.workspaceController.activeTab
                    const type = centerPanel.workspaceController.activeTabType
                    // TagPanel's inline control contexts are sensitive to cancellation
                    // during incubation. Build that lightweight shell atomically;
                    // metadata reading and delegate population remain deferred.
                    asynchronous = type !== "tag"
                    sourceComponent = type === "manual" ? manualComponent
                        : type === "settings" ? settingsComponent
                        : type === "pacs" ? pacsComponent
                        : type === "tag" ? tagComponent
                        : type === "3d" ? volumeComponent
                        : type === "montage" ? montageComponent : imageComponent
                    active = true
                }
                Component.onCompleted: openCurrentTab()
                Connections {
                    target: centerPanel.workspaceController
                    function onActiveTabChanged() { workspaceLoader.openCurrentTab() }
                }
            }
            WorkspaceLoadingState {
                anchors.fill: parent
                visible: centerPanel.hasTabs && (workspaceLoader.status !== Loader.Ready
                    || centerPanel.opening?.status === "loading" || centerPanel.opening?.status === "error")
                loading: workspaceLoader.status !== Loader.Error && centerPanel.opening?.status !== "error"
                message: workspaceLoader.status === Loader.Error ? "视图界面加载失败"
                    : centerPanel.opening?.status === "error" ? centerPanel.opening.errorMessage
                    : workspaceLoader.status !== Loader.Ready ? "正在打开视图…"
                    : (centerPanel.opening?.message ?? "正在准备影像…")
                onRetryRequested: {
                    if (workspaceLoader.status === Loader.Error) workspaceLoader.openCurrentTab()
                    centerPanel.workspaceController.retryActiveTab()
                }
                onCloseRequested: centerPanel.workspaceController.closeTab(centerPanel.workspaceController.activeTabId)
            }
        }

    }

    Component {
        id: manualComponent
        Manual.OperationManual {
            controller: centerPanel.workspaceController.manualController
            active: centerPanel.workspaceController.activeTabType === "manual"
                && workspaceLoader.status === Loader.Ready
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
            active: workspaceLoader.status === Loader.Ready
            tagController: workspaceLoader.loadedTab
                ? workspaceLoader.loadedTab.tagController
                : null
        }
    }

    Component {
        id: imageComponent
        ViewportSection.ViewportLayout {
            // Loader and workspace signals can update in different orders.
            // Never hand a volume controller to a still-live image component.
            viewportController: centerPanel.imageWorkspace
                && centerPanel.viewportController?.setViewportSize !== undefined
                ? centerPanel.viewportController : null
            hasTabs: centerPanel.hasTabs
            tabType: centerPanel.workspaceController.activeTabType
            currentTabAllViewports: centerPanel.imageWorkspace
                ? centerPanel.currentTabAllViewports.filter(view => view?.setViewportSize !== undefined) : []
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
