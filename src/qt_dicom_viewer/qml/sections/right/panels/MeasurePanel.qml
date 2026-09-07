pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../components" as Components
import "../../../theme"

ColumnLayout {
    id: measurePanel
    spacing: 8
    required property var toolController

    signal actionTriggered(string action)

    Text {
        Layout.fillWidth: true
        text: "Esc 取消绘制 · Delete / Backspace 删除选中测量"
        color: Theme.textSubtle
        font.pixelSize: 11
        wrapMode: Text.Wrap
    }

    GridLayout {
        Layout.fillWidth: true
        columns: 2
        columnSpacing: 6
        rowSpacing: 6
        uniformCellWidths: true
        Repeater {
            model: measurePanel.toolController ? measurePanel.toolController.measureActions : []
            delegate: Components.ToolActionButton {
                id: measureButton
                required property var modelData
                readonly property bool btnChecked: measureButton.modelData.action === measurePanel.toolController.activeInteraction

                checked: measureButton.btnChecked
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                iconName: modelData.iconName
                label: modelData.label

                onClicked: {
                    measurePanel.actionTriggered(modelData.action);
                }
            }
        }
    }

    Item {
        Layout.fillHeight: true
    }
}
