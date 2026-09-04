pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import "../components" as Components
import "../theme"

Item {
    id: sidebar
    objectName: "sidebarContainer"
    required property var panelController
    readonly property real minimumExpandedWidth: 200
    readonly property real maximumExpandedWidth: 350
    property real expandedWidth: 300
    property bool collapsed: false
    property bool resizing: false
    implicitWidth: collapsed ? 0 : expandedWidth
    z: 10

    function resizeTo(candidate) {
        if (candidate < minimumExpandedWidth) {
            collapsed = true
        } else {
            expandedWidth = Math.min(maximumExpandedWidth, candidate)
            collapsed = false
        }
    }

    LeftPanel {
        anchors.fill: parent
        visible: !sidebar.collapsed
        panelController: sidebar.panelController
    }

    Rectangle {
        anchors.right: parent.right
        anchors.rightMargin: 2
        anchors.verticalCenter: parent.verticalCenter
        width: 1
        height: parent.height - 16
        visible: !sidebar.collapsed && (resizeArea.containsMouse || sidebar.resizing)
        color: Theme.borderStrong
    }

    MouseArea {
        id: resizeArea
        objectName: "sidebarResizeHandle"
        x: sidebar.width - width / 2
        width: 10
        height: parent.height
        visible: !sidebar.collapsed || sidebar.resizing
        hoverEnabled: true
        cursorShape: Qt.SizeHorCursor
        preventStealing: true
        property real pressX: 0
        property real pressWidth: 0
        onPressed: mouse => {
            pressX = mapToItem(null, mouse.x, mouse.y).x
            pressWidth = sidebar.width
            sidebar.resizing = true
        }
        onPositionChanged: mouse => {
            if (pressed)
                sidebar.resizeTo(pressWidth + mapToItem(null, mouse.x, mouse.y).x - pressX)
        }
        onReleased: sidebar.resizing = false
        onCanceled: sidebar.resizing = false
    }

    Components.AppButton {
        objectName: "sidebarToggle"
        x: sidebar.collapsed ? sidebar.width + 8 : sidebar.width - width - 2
        anchors.verticalCenter: parent.verticalCenter
        width: 20
        height: 32
        minimumButtonWidth: 20
        compact: true
        momentary: true
        text: sidebar.collapsed ? "›" : "‹"
        textColor: hovered || down ? Theme.textMuted : Theme.textSubtle
        normalColor: Theme.panelBackgroundStrong
        hoverColor: Theme.controlBackground
        pressedColor: Theme.secondarySoft
        activeColor: Theme.controlBackground
        focusBorderColor: Theme.borderDefault
        activeBorderColor: Theme.borderDefault
        cornerRadius: 4
        onClicked: sidebar.collapsed = !sidebar.collapsed
        Basic.ToolTip.visible: hovered
        Basic.ToolTip.delay: 600
        Basic.ToolTip.text: sidebar.collapsed ? "展开侧栏" : "收起侧栏"
    }
}
