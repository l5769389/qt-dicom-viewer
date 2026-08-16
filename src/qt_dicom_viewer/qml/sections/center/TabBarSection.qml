pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts

Basic.TabBar {
            id: workspaceTabs

            required property var workspaceController
            readonly property int tabWidth: 180
            spacing: 2

            background: Rectangle {
                color: "#1d222a"

                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 1
                    color: "#303744"
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
                        spacing: 8

                        Text {
                            Layout.fillWidth: true
                            text: tabButton.modelData.tabLabel
                            color: tabButton.checked ? "#f4f8fb" : "#9aa5b3"
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

                            contentItem: Text {
                                text: closeButton.text
                                color: closeButton.hovered ? "#ffffff" : "#808b98"
                                font.pixelSize: 16
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }

                            background: Rectangle {
                                color: closeButton.hovered ? "#3b424d" : "transparent"
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
                            ? "#272e38"
                            : tabButton.hovered ? "#232933" : "transparent"

                        Rectangle {
                            visible: tabButton.checked
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            height: 2
                            color: "#58a8df"
                        }
                    }
                }
            }
        }