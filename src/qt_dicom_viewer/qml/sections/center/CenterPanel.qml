pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import 'viewportArea' as ViewportSection

Rectangle {
    id: centerPanel

    required property var workspaceController
    required property var panelController
    required property var activeViewport

    readonly property bool hasTabs:
        workspaceController.tabs.length > 0

    color: "#15191f"
    border.color: "#303744"
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
            workspaceController: centerPanel.workspaceController
        }

        ViewportSection.Viewport {
            Layout.fillWidth: true
            Layout.fillHeight: true
            activeViewport: centerPanel.activeViewport
            hasTabs: centerPanel.hasTabs
        }

    }

    WorkspaceEmptyState {
        anchors.fill: parent
        visible: !centerPanel.hasTabs
        panelController: centerPanel.panelController
    }
}
