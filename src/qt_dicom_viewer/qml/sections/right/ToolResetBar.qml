pragma ComponentBehavior: Bound
import QtQuick
import "components" as Controls
import "../../theme"
Rectangle {
    id: root
    required property var toolController
    implicitHeight: 52
    color: Theme.panelBackgroundStrong
    Controls.ToolActionButton {
        objectName: "activeToolReset"
        anchors.fill: parent; anchors.margins: 6
        iconName: "reset"
        label: root.toolController ? root.toolController.resetLabel : "暂无可重置内容"
        enabled: root.toolController ? root.toolController.canResetActiveTool : false
        hoverColor: Theme.resetActionHover
        pressedColor: Theme.resetActionPressed
        onClicked: root.toolController.resetActiveTool()
    }
}
