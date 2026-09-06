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
        color: Theme.panelBackgroundStrong

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 1
            color: Theme.dividerColor
        }
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
                    Layout.preferredWidth: Math.max(
                        30,
                        tabTypeLabel.implicitWidth + 12
                    )
                    Layout.preferredHeight: 22
                    radius: 5
                    color: tabButton.checked
                        ? Theme.primarySoft
                        : Theme.secondarySoft
                    border.color: tabButton.checked
                        ? Theme.selectionBorder
                        : "transparent"
                    border.width: 1

                    Text {
                        id: tabTypeLabel

                        anchors.centerIn: parent
                        font.pixelSize: 11
                        text: String(
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
                radius: 5
                color: tabButton.checked
                    ? Theme.elevatedBackground
                    : tabButton.hovered
                        ? Theme.controlHover
                        : "transparent"

                Rectangle {
                    visible: tabButton.checked
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 2
                    color: Theme.activeIndicator
                }
            }
        }
    }
}
