pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../theme"

Basic.TabBar {
    id: workspaceTabs

    required property var workspaceController
    readonly property int tabWidth: 180
    spacing: 2

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

        delegate: Basic.TabButton
        {
            required property var modelData

            id: tabButton
            width: tabWidth
            implicitWidth: tabWidth
            checked: tabButton.modelData.tabId
                === workspaceTabs.workspaceController.activeTabId

            onClicked: {
                workspaceTabs.workspaceController.activateTabId(
                    tabButton.modelData.tabId
                )
            }
            contentItem: RowLayout {
                id: tabContent
                spacing: 2

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

                Rectangle {
                    radius: 6
                    Layout.fillHeight: true
                    width: 30
                    color: tabButton.checked
                        ? Theme.selectionBackground
                        : Theme.secondarySoft
                    border.color: tabButton.checked
                        ? Theme.selectionBorder
                        : Theme.borderSubtle
                    border.width: 1
                    Text {
                        anchors.centerIn: parent
                        font.pixelSize: 12
                        text: tabButton.modelData.tabType
                        font.weight: tabButton.checked
                            ? Font.DemiBold : Font.Normal
                        elide: Text.ElideRight
                        color: tabButton.checked
                            ? Theme.primaryColor
                            : Theme.textSecondary

                    }
                }

                Basic.ToolButton {
                    id: closeButton
                    text: "×"
                    implicitWidth: 24
                    implicitHeight: 24

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
                color: tabButton.checked
                    ? Theme.selectionBackground
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
