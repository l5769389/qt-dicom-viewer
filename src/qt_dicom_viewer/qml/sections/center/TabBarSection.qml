pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../theme"

Basic.TabBar {
    id: workspaceTabs

    required property var workspaceController
    readonly property int tabCount:
        workspaceTabs.workspaceController.tabs.length
    readonly property real tabWidth: Math.min(
        200,
        Math.max(
            136,
            (workspaceTabs.width - 8
                - Math.max(0, workspaceTabs.tabCount - 1)
                    * workspaceTabs.spacing)
                / Math.max(1, workspaceTabs.tabCount)
        )
    )
    spacing: 3
    leftPadding: 6

    background: Rectangle {
        // 与下方留白使用同一工作区底色，避免色阶交界看起来像横向边框。
        color: Theme.workspaceBackground
    }

    Repeater {
        model: workspaceTabs.workspaceController.tabs

        delegate: Basic.TabButton {
            required property var modelData

            id: tabButton
            width: workspaceTabs.tabWidth
            implicitWidth: workspaceTabs.tabWidth
            leftPadding: 10
            rightPadding: 6
            topPadding: 6
            bottomPadding: 6
            checked: tabButton.modelData.tabId
                === workspaceTabs.workspaceController.activeTabId

            onClicked: {
                workspaceTabs.workspaceController.activateTabId(
                    tabButton.modelData.tabId
                )
            }
            contentItem: RowLayout {
                id: tabContent
                spacing: 7

                // 视图类型先作为上下文标识，再显示序列名称。
                Rectangle {
                    Layout.preferredWidth:
                        String(tabButton.modelData.tabType).toLowerCase()
                            === "petctfusion" ? 60
                        : String(tabButton.modelData.tabType).toLowerCase() === "mpr" ? 38 : 30
                    Layout.preferredHeight: 22
                    radius: 5
                    color: tabButton.checked
                        ? Theme.primaryStrong
                        : Theme.secondarySoft
                    border.color: tabButton.checked
                        ? "transparent"
                        : "transparent"
                    border.width: 0

                    Text {
                        anchors.centerIn: parent
                        font.pixelSize: 11
                        text: String(tabButton.modelData.tabType).toLowerCase() === "petctfusion" ? "PET/CT" : String(
                            tabButton.modelData.tabType
                        ).toUpperCase()
                        font.weight: tabButton.checked
                            ? Font.DemiBold : Font.Normal
                        color: tabButton.checked
                            ? Theme.textOnPrimary
                            : Theme.textMuted
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: tabButton.modelData.tabLabel
                    color: tabButton.checked
                        ? Theme.textPrimary
                        : Theme.textMuted
                    font.pixelSize: 12
                    font.weight: tabButton.checked
                        ? Font.DemiBold : Font.Normal
                    elide: Text.ElideRight
                    verticalAlignment: Text.AlignVCenter
                }

                Basic.ToolButton {
                    id: closeButton
                    text: "×"
                    implicitWidth: 24
                    implicitHeight: 24
                    opacity: tabButton.checked
                        || tabButton.hovered
                        || closeButton.hovered ? 1 : 0
                    enabled: opacity > 0.5

                    Behavior on opacity {
                        NumberAnimation { duration: 100 }
                    }

                    contentItem: Text {
                        text: closeButton.text
                        color: closeButton.hovered
                            ? Theme.textPrimary
                            : Theme.textSubtle
                        font.pixelSize: 16
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    background: Rectangle {
                        color: closeButton.hovered
                            ? Theme.controlHover
                            : "transparent"
                        radius: 4
                    }

                    onClicked: {
                        workspaceTabs.workspaceController.closeTab(
                            tabButton.modelData.tabId
                        )
                    }
                }
            }

            background: Rectangle {
                radius: 6
                color: tabButton.checked
                    ? Theme.selectionBackground
                    : tabButton.hovered
                        ? Theme.controlHover
                        : "transparent"
                border.color: tabButton.checked
                    ? Theme.controlHoverBorder
                    : "transparent"
                border.width: tabButton.checked ? 1 : 0
            }
        }
    }
}
