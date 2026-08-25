pragma ComponentBehavior: Bound
import "../components" as Components

import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: measurePanel
    spacing: 8
    required property var toolController

    signal actionTriggered(string action)

    Components.ToolPanelHeader {
        Layout.fillWidth: true
        Layout.bottomMargin: 4
        iconName: "measure"
        title: "测量"
    }

    Repeater {
        model: measurePanel.toolController
            ? measurePanel.toolController.measureActions
            : []
        delegate: Components.ToolActionButton
        {
            id: measureButton
            required property var modelData
            readonly  property bool btnChecked : measureButton.modelData.action === toolController.activeInteraction

            checked:measureButton.btnChecked
            Layout.fillWidth: true
            iconName: modelData.iconName
            label: modelData.label

            onClicked: {
                measurePanel.actionTriggered(modelData.action)
            }

            background: Rectangle {
                color: measureButton.checked ? "#253b4b" : measureButton.hovered ? "#252c35" : "transparent"
                border.color: measureButton.checked ? "#3d7599" : "transparent"
                border.width: 1
                radius: 6
            }
        }
    }

    Item {
        Layout.fillHeight: true
    }
}
