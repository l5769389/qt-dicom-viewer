pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "../components" as Components

ColumnLayout {
    id: rotatePanel

    required property var toolController
    signal actionTriggered(string action)
    spacing: 8

    Repeater {
        model: rotatePanel.toolController
            ? rotatePanel.toolController.rotateActions
            : []

        delegate: Components.ToolActionButton
        {
            required property var modelData

            Layout.fillWidth: true
            iconName: modelData.iconName
            label: modelData.label

            onClicked: {
                rotatePanel.actionTriggered(modelData.action)
            }
        }
    }

    Item {
        Layout.fillHeight: true
    }
}
