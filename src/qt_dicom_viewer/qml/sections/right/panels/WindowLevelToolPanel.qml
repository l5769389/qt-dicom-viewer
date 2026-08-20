pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "../components" as Components
import QtQuick.Controls.Basic as Basic
ColumnLayout {
    id: windowPanel

    required property var presets
    signal actionTriggered(
                string presetId,
        real center,
        real width
    )


    Components.ToolPanelHeader {
        Layout.fillWidth: true
        iconName: "window"
        title: "窗宽窗位"
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 30
        color: "#20262e"
        radius: 4

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 10

            Text {
                Layout.fillWidth: true
                text: "预设"
                color: "#8f9ba8"
            }

            Text {
                Layout.preferredWidth: 55
                text: "WL"
                color: "#8f9ba8"
                horizontalAlignment: Text.AlignRight
            }

            Text {
                Layout.preferredWidth: 55
                text: "WW"
                color: "#8f9ba8"
                horizontalAlignment: Text.AlignRight
            }
        }
    }

    ListView {
        id: presetList

        Layout.fillWidth: true
        Layout.fillHeight: true
        spacing: 4
        clip: true
        model: windowPanel.presets

        delegate: Basic.ItemDelegate {
            id: presetItem

            required property var modelData

            width: presetList.width
            height: 38

            onClicked: {
                windowPanel.actionTriggered(
                    modelData.presetId,
                    Number(modelData.center),
                    Number(modelData.width)
                )
            }

            contentItem: RowLayout {
                spacing: 8

                Text {
                    Layout.fillWidth: true
                    text: presetItem.modelData.label
                    color: "#d7e0e8"
                    elide: Text.ElideRight
                }

                Text {
                    Layout.preferredWidth: 55
                    text: presetItem.modelData.center
                    color: "#aab5c0"
                    horizontalAlignment: Text.AlignRight
                }

                Text {
                    Layout.preferredWidth: 55
                    text: presetItem.modelData.width
                    color: "#aab5c0"
                    horizontalAlignment: Text.AlignRight
                }
            }

            background: Rectangle {
                color: presetItem.pressed
                    ? "#29475a"
                    : presetItem.hovered
                        ? "#242c35"
                        : "transparent"
                radius: 5
            }
        }
    }
}