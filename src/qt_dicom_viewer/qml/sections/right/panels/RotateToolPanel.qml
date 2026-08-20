pragma
ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "../components" as Components

ColumnLayout {
    id: rotatePanel

    required property var toolController
    signal actionTriggered(string action)
    spacing: 8

    Components.ToolPanelHeader {
        Layout.fillWidth: true
        Layout.bottomMargin: 4
        iconName: "rotate"
        title: "旋转与镜像"
    }

    Repeater {
        model: toolController.rotateActions

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
