pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"

Rectangle {
    id: resetBar

    required property var toolController
    property var voiController: null
    readonly property string panel: toolController?.activePanel ?? ""
    readonly property bool voiActions: !!voiController && (panel === "segmentation" || panel === "voi")

    implicitHeight: 52
    color: Theme.panelBackgroundStrong
    radius: Theme.controlRadius

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 1
        color: Theme.dividerColor
    }

    Basic.Button {
        id: resetButton
        objectName: "activeToolReset"
        visible: !resetBar.voiActions

        anchors.fill: parent
        anchors.margins: 10
        enabled: resetBar.toolController
            ? resetBar.toolController.canResetActiveTool
            : false

        onClicked: {
            if (resetBar.toolController)
                resetBar.toolController.resetActiveTool()
        }

        contentItem: RowLayout {
            spacing: 9

            Components.AppIcon {
                iconName: "reset"
                iconSize: 19
                iconColor: resetButton.enabled
                    ? Theme.resetActionColor
                    : Theme.textDisabled
            }

            Text {
                Layout.fillWidth: true
                text: resetBar.toolController
                    ? resetBar.toolController.resetLabel
                    : "暂无可重置内容"
                color: resetButton.enabled
                    ? Theme.textSecondary
                    : Theme.textDisabled
                font.pixelSize: 12
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        background: Rectangle {
            radius: 6
            color: !resetButton.enabled
                ? Theme.controlDisabled
                : resetButton.down
                    ? Theme.resetActionPressed
                    : resetButton.hovered
                        ? Theme.resetActionHover
                        : Theme.controlBackground
            border.width: resetButton.activeFocus ? 2 : 1
            border.color: resetButton.enabled
                ? (resetButton.activeFocus ? Theme.focusBorder : Theme.controlBorder)
                : Theme.controlBorder
        }
    }

    RowLayout {
        objectName: "voiBottomActions"
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8
        visible: resetBar.voiActions
        Components.AppButton {
            objectName: "voiClearKind"
            Layout.fillWidth: true
            compact: true
            text: resetBar.panel === "segmentation" ? "清除分割" : "清除 VOI"
            enabled: (resetBar.voiController?.items ?? []).some(item => item.kind === resetBar.panel)
            onClicked: resetBar.voiController.clear(resetBar.panel)
        }
        Components.AppButton {
            objectName: "voiClearAll"
            Layout.fillWidth: true
            compact: true
            text: "全部清除"
            textColor: Theme.warningColor
            enabled: (resetBar.voiController?.items.length ?? 0) > 0
            onClicked: resetBar.voiController.clear("")
        }
    }
}
