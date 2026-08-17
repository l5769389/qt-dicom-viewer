pragma
ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import 'viewportArea' as ViewportSection

Rectangle {
    id: centerPanel

    required property var workspaceController
    readonly property bool hasTabs: workspaceController.tabs.length > 0
    readonly property var activeViewport:
            workspaceController.activeViewports.length > 0
        ? workspaceController.activeViewports[0]
        : null

    color: "#15191f"
    border.color: "#303744"
    border.width: 1
    radius: 8
    clip: true

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

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
}
