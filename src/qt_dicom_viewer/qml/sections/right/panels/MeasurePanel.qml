pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../components" as Components
import "../../../theme"

ColumnLayout {
    id: measurePanel
    spacing: 8
    required property var toolController

    signal manualRequested()

    Components.ToolActionButton {
        objectName: "measurementManualButton"
        Layout.alignment: Qt.AlignRight
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
        iconName: "manual"
        iconSize: 18
        label: "测量操作手册"
        onClicked: measurePanel.manualRequested()
    }

    signal actionTriggered(string action)

    Text {
        Layout.fillWidth: true
        text: "松开为选中已完成，点击为选中草稿\n"
            + (Qt.platform.os === "osx" ? "⌘+C / ⌘+V" : "Ctrl+C / Ctrl+V") + " 复制 / 粘贴所选\n"
            + "Esc 取消绘制 · Delete / Backspace 删除"
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
                readonly property bool btnChecked: measureButton.modelData.action === (measurePanel.toolController?.activeInteraction ?? "")

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
