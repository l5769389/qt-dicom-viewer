import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "sections" as Sections
import "sections/center" as CenterSections
import "theme"
import "components" as Components

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
    readonly property bool nativeTitleBar: Qt.platform.os === "windows"
    flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint
        | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint
        | (nativeTitleBar ? 0
            : Qt.WindowFullscreenButtonHint | Qt.ExpandedClientAreaHint | Qt.NoTitleBarBackgroundHint)
    topPadding: header ? header.height : 32
    function toggleFullScreen() {
        if (visibility === Window.FullScreen) showNormal()
        else showFullScreen()
    }
    Shortcut {
        sequence: Qt.platform.os === "osx" ? "Ctrl+Meta+F" : "F11"
        onActivated: window.toggleFullScreen()
    }
    Component.onCompleted: {
        if (typeof appController.configureNativeWindow === "function")
            appController.configureNativeWindow(window)
    }
    visible: true
    title: "Voxenra"
    color: Theme.appBackground

    header: Components.ApplicationTitleBar {
        targetWindow: window
        // Windows owns the only caption, including branding and hit testing.
        visible: !window.nativeTitleBar
        height: visible ? implicitHeight : 0
    }
    Shortcut {
        sequences: [StandardKey.Open]
        enabled: window.pacsController?.localEnabled !== false && !window.panelController.scanning
        onActivated: window.panelController.openImportDialog()
    }
    RowLayout {
        id: workspaceRow
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        Sections.SidebarContainer {
            id: seriesSidebar
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
            Layout.minimumWidth: 360
            Layout.fillWidth: true
            Layout.fillHeight: true
            workspaceController: window.workspaceController
            panelController: window.panelController
            pacsController: window.pacsController
            settingsController: appController.settingsController ?? null
            currentTabAllViewports: window.currentTabAllViewports
            viewportController: window.viewportController
        }

        Components.WidthResizeHandle {
            objectName: "rightPanelResizeHandle"
            visible: rightPanel.visible
            Layout.preferredWidth: 8
            Layout.fillHeight: true
            currentWidth: rightPanel.width
            minimumWidth: 220
            maximumWidth: rightPanel.widthLimit
            direction: -1
            onWidthDragged: value => rightPanel.dragWidth = value
            onWidthCommitted: value => {
                appController.settingsController?.setValue("layout", "rightPanelWidth", Math.round(value))
                rightPanel.dragWidth = -1
            }
        }
        Sections.RightPanel {
            id: rightPanel
            property real dragWidth: -1
            readonly property real widthLimit: Math.max(220, Math.min(420,
                workspaceRow.width - seriesSidebar.width - 360 - 8 - workspaceRow.spacing * 3))
            readonly property real desiredWidth: dragWidth >= 0 ? dragWidth
                : (appController.settingsController?.values.layout.rightPanelWidth ?? 250)
            readonly property real actualWidth: Math.min(widthLimit, desiredWidth)
            enabled: !["loading", "error"].includes(window.workspaceController.activeLoadState?.status ?? "")
            onManualRequested: chapter => window.workspaceController.openManual(chapter)
            exportController: appController.exportController ?? null
            exportItem: centerView.exportItem
            visible: window.hasTabs && ["tag", "settings", "pacs", "manual"].indexOf(window.workspaceController.activeTabType) < 0
            Layout.minimumWidth: visible ? actualWidth : 0
            Layout.preferredWidth: visible ? actualWidth : 0
            Layout.maximumWidth: visible ? actualWidth : 0
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
    DropArea {
        id: fileDrop
        objectName: "dicomFileDropArea"
        anchors.fill: parent
        enabled: window.pacsController?.localEnabled !== false
        onEntered: drag => {
            if (drag.hasUrls && window.panelController.canImportUrls(drag.urls)
                    && (drag.supportedActions & Qt.CopyAction)) drag.accept(Qt.CopyAction)
            else drag.accepted = false
        }
        onDropped: drop => {
            if (drop.hasUrls && (drop.supportedActions & Qt.CopyAction)
                    && window.panelController.importUrls(drop.urls)) drop.accept(Qt.CopyAction)
            else drop.accepted = false
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: 10
            visible: fileDrop.containsDrag
            color: "#b3101d27"
            border.width: 2
            border.color: Theme.primaryColor
            radius: 8
            Column {
                anchors.centerIn: parent
                spacing: 8
                Text { anchors.horizontalCenter: parent.horizontalCenter; text: "松开以导入 DICOM"; color: Theme.textPrimary; font.pixelSize: 22 }
                Text { anchors.horizontalCenter: parent.horizontalCenter; text: "文件、文件夹或 ZIP / RAR / 7z / TAR / GZ 压缩包"; color: Theme.textMuted; font.pixelSize: 13 }
            }
        }
    }
    Sections.ImportTaskDialog {
        controller: window.panelController
    }
    Sections.ExportDialog {
        controller: window.seriesExportController
        settingsController: appController.settingsController ?? null
    }
}
