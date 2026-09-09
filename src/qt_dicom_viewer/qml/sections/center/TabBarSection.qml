pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../theme"
import "../../components" as Components

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
            objectName: "workspaceTab-" + tabButton.modelData.tabId
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

                Basic.BusyIndicator {
                    objectName: "tabLoading-" + tabButton.modelData.tabId
                    Layout.preferredWidth: 14
                    Layout.preferredHeight: 14
                    visible: workspaceTabs.workspaceController.loadingStates[tabButton.modelData.tabId] === "loading"
                    running: visible
                }

                // 视图类型先作为上下文标识，再显示序列名称。
                Rectangle {
                    Layout.preferredWidth: Math.max(
                        30,
                        tabTypeLabel.implicitWidth + 12
                    )
                    Layout.preferredHeight: 22
                    radius: 5
                    color: tabButton.checked
                        ? Theme.selectionBackground
                        : Theme.secondarySoft
                    border.color: tabButton.checked
                        ? "transparent"
                        : "transparent"
                    border.width: 0

                    Components.AppIcon {
                        anchors.centerIn: parent
                        visible: ["settings", "manual"].includes(String(tabButton.modelData.tabType).toLowerCase())
                        iconName: String(tabButton.modelData.tabType).toLowerCase() === "manual" ? "manual" : "settings"
                        iconSize: 14
                        iconColor: tabButton.checked ? Theme.primaryColor : Theme.iconDefault
                    }
                    Text {
                        id: tabTypeLabel

                        anchors.centerIn: parent
                        font.pixelSize: 11
                        text: ["settings", "manual"].includes(String(tabButton.modelData.tabType).toLowerCase()) ? "" : String(tabButton.modelData.tabType).toLowerCase() === "petctfusion" ? "PET/CT" : String(
                            tabButton.modelData.tabType
                        ).toUpperCase()
                        font.weight: tabButton.checked
                            ? Font.DemiBold : Font.Normal
                        color: tabButton.checked
                            ? Theme.primaryColor
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
                    Accessible.name: "关闭 " + tabButton.modelData.tabLabel
                    implicitWidth: 24
                    implicitHeight: 24
                    opacity: tabButton.checked
                        || tabButton.hovered
                        || closeButton.hovered || closeButton.activeFocus ? 1 : 0

                    Behavior on opacity {
                        NumberAnimation { duration: 100 }
                    }

                    contentItem: Item {
                        Components.AppIcon {
                            anchors.centerIn: parent
                            iconName: "close"
                            iconSize: 16
                            iconColor: closeButton.hovered ? Theme.iconHover : Theme.iconDefault
                        }
                    }

                    background: Rectangle {
                        color: closeButton.hovered
                            ? Theme.controlHover
                            : "transparent"
                        radius: 4
                        border.width: closeButton.activeFocus ? 1 : 0
                        border.color: Theme.focusBorder
                    }

                    onClicked: {
                        workspaceTabs.workspaceController.closeTab(
                            tabButton.modelData.tabId
                        )
                    }
                }
            }

            background: Rectangle {
                objectName: "workspaceTabBackground-" + tabButton.modelData.tabId
                readonly property color visualBorderColor: tabButton.checked
                    ? Theme.controlHoverBorder : Theme.borderSubtle
                radius: 6
                color: tabButton.checked
                    ? Theme.selectionBackground
                    : tabButton.hovered
                        ? Theme.controlHover
                        : Theme.panelBackgroundSoft
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.leftMargin: 6
                    anchors.rightMargin: 6
                    height: 2
                    visible: tabButton.checked
                    color: Theme.activeIndicator
                }
                border.color: tabButton.activeFocus ? Theme.focusBorder : visualBorderColor
                border.width: 1
            }
        }
    }
}
