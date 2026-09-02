pragma
ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../../../theme"

ColumnLayout {
    id: windowPanel

    required property var presets

    signal actionTriggered(
        string presetId,
        real center,
        real width
    )


    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 30
        Layout.maximumHeight: 30
        color: Theme.secondarySoft
        radius: 4

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 10

            Text {
                Layout.fillWidth: true
                text: "预设"
                color: Theme.textMuted
            }

            Text {
                Layout.preferredWidth: 55
                text: "WL"
                color: Theme.textMuted
                horizontalAlignment: Text.AlignRight
            }

            Text {
                Layout.preferredWidth: 55
                text: "WW"
                color: Theme.textMuted
                horizontalAlignment: Text.AlignRight
            }
        }
    }

    ListView {
        id: presetList

        Layout.fillWidth: true
        Layout.preferredHeight: contentHeight
        Layout.maximumHeight: contentHeight
        implicitHeight: contentHeight
        spacing: 4
        clip: true
        interactive: false
        model: windowPanel.presets

        delegate: Basic.ItemDelegate
        {
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
                    color: Theme.textPrimary
                    elide: Text.ElideRight
                }

                Text {
                    Layout.preferredWidth: 55
                    text: presetItem.modelData.center
                    color: Theme.textSecondary
                    horizontalAlignment: Text.AlignRight
                }

                Text {
                    Layout.preferredWidth: 55
                    text: presetItem.modelData.width
                    color: Theme.textSecondary
                    horizontalAlignment: Text.AlignRight
                }
            }

            background: Rectangle {
                color: presetItem.pressed
                    ? Theme.controlPressed
                    : presetItem.hovered
                        ? Theme.controlHover
                        : "transparent"
                radius: 5
            }
        }
    }
    Item {
        Layout.fillHeight: true
    }
}
