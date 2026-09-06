pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"

Rectangle {
    id: resetBar

    required property var toolController

    implicitHeight: 62
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
                    ? Theme.resetActionColor
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
                        : Theme.resetActionSurface
            border.width: 1
            border.color: resetButton.enabled
                ? Theme.resetActionBorder
                : Theme.controlBorder
        }
    }
}
