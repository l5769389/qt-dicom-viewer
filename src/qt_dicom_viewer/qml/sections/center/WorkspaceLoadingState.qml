pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"

Rectangle {
    id: root
    objectName: "workspaceLoadingState"
    property bool loading: true
    property string message: "正在打开视图…"
    signal retryRequested()
    signal closeRequested()
    color: Theme.workspaceBackground
    Accessible.name: message

    // Block the unfinished image, while the tab strip and sidebar stay usable.
    MouseArea { anchors.fill: parent; acceptedButtons: Qt.AllButtons; onWheel: wheel => wheel.accepted = true }
    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(360, Math.max(0, parent.width - 40))
        spacing: 14
        Basic.BusyIndicator {
            objectName: "workspaceBusyIndicator"
            Layout.alignment: Qt.AlignHCenter
            running: root.loading && root.visible
            visible: root.loading
            implicitWidth: 36
            implicitHeight: 36
        }
        Text {
            objectName: "workspaceLoadingMessage"
            Layout.fillWidth: true
            text: root.message
            color: root.loading ? Theme.textSecondary : Theme.dangerColor
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            font.pixelSize: 13
        }
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 10
            Components.AppButton {
                objectName: "retryWorkspaceLoad"
                visible: !root.loading
                text: "重试"
                normalColor: Theme.primaryButtonBackground
                hoverColor: Theme.primaryButtonHover
                onClicked: root.retryRequested()
            }
            Components.AppButton {
                objectName: "cancelWorkspaceLoad"
                text: root.loading ? "取消打开" : "关闭页签"
                normalColor: "transparent"
                onClicked: root.closeRequested()
            }
        }
    }
}
