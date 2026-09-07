pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "components" as Controls
import "../../theme"
Rectangle {
    id: root
    required property var toolController
    property var voiController: null
    readonly property string panel: toolController?.activePanel ?? ""
    readonly property bool voiActions: !!voiController && ["segmentation", "voi"].includes(panel)
    implicitHeight: 52
    color: Theme.panelBackgroundStrong
    Controls.ToolActionButton {
        objectName: "activeToolReset"
        visible: !root.voiActions
        anchors.fill: parent; anchors.margins: 6
        iconName: "reset"
        label: root.toolController ? root.toolController.resetLabel : "暂无可重置内容"
        enabled: root.toolController ? root.toolController.canResetActiveTool : false
        hoverColor: Theme.resetActionHover
        pressedColor: Theme.resetActionPressed
        onClicked: root.toolController.resetActiveTool()
    }
    RowLayout {
        objectName: "voiBottomActions"
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8
        visible: root.voiActions
        Components.AppButton {
            objectName: "voiClearKind"
            Layout.fillWidth: true
            compact: true
            text: root.panel === "segmentation" ? "清除分割" : "清除 VOI"
            enabled: (root.voiController?.items ?? []).some(item => item.kind === root.panel)
            onClicked: root.voiController.clear(root.panel)
        }
        Components.AppButton {
            objectName: "voiClearAll"
            Layout.fillWidth: true
            compact: true
            text: "全部清除"
            textColor: Theme.warningColor
            enabled: (root.voiController?.items.length ?? 0) > 0
            onClicked: root.voiController.clear("")
        }
    }
}
