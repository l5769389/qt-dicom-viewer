pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../components" as Components
import "../theme"

Basic.Dialog {
    id: dialog
    objectName: "importTaskDialog"
    required property var controller
    parent: Basic.Overlay.overlay
    anchors.centerIn: parent
    // A separate popup window stays above native VTK hosts as well as QML views.
    popupType: Basic.Popup.Window
    // Native popup geometry must not inherit changing text/layout size hints.
    implicitWidth: 460
    implicitHeight: 280
    width: Math.min(implicitWidth, parent ? parent.width - 32 : implicitWidth)
    height: Math.min(implicitHeight, parent ? parent.height - 32 : implicitHeight)
    modal: false
    padding: 20
    closePolicy: controller.scanning ? Basic.Popup.NoAutoClose : Basic.Popup.CloseOnEscape
    onClosed: controller.closeImportTask()
    Connections {
        target: dialog.controller
        function onImportTaskChanged() {
            if (dialog.controller.importTaskOpen && !dialog.opened) dialog.open()
            else if (!dialog.controller.importTaskOpen) dialog.close()
        }
    }
    Timer {
        interval: 4000
        running: dialog.visible && !dialog.controller.scanning && !dialog.controller.importError
        onTriggered: dialog.close()
    }
    background: Rectangle {
        color: Theme.panelBackgroundStrong
        border.color: Theme.borderStrong
        radius: 8
    }
    header: Text {
        text: dialog.controller.scanning ? "正在导入影像"
            : dialog.controller.importError ? "导入未完成" : "导入结果"
        color: Theme.textPrimary
        font.pixelSize: 18
        font.bold: true
        leftPadding: 20; rightPadding: 20; topPadding: 20; bottomPadding: 10
    }
    contentItem: ColumnLayout {
        implicitWidth: 0
        implicitHeight: 0
        spacing: 10
        Basic.ScrollView {
            id: messageArea
            objectName: "importTaskMessageArea"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: 0
            Layout.minimumHeight: 40
            clip: true
            contentWidth: availableWidth
            Basic.ScrollBar.horizontal.policy: Basic.ScrollBar.AlwaysOff
            Basic.ScrollBar.vertical.policy: Basic.ScrollBar.AsNeeded
            Basic.TextArea {
                objectName: "importTaskMessage"
                width: messageArea.availableWidth
                implicitWidth: 0
                padding: 0
                rightPadding: messageArea.effectiveScrollBarWidth
                readOnly: true
                selectByMouse: true
                text: dialog.controller.statusMessage
                textFormat: TextEdit.PlainText
                color: dialog.controller.importError ? "#ffb4a9" : Theme.textPrimary
                font.pixelSize: 13
                wrapMode: TextEdit.Wrap
                background: null
            }
        }
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 12
            Basic.ProgressBar {
                objectName: "importTaskProgress"
                anchors.fill: parent
                visible: dialog.controller.scanning
                indeterminate: dialog.controller.importProgress < 0
                value: Math.max(0, dialog.controller.importProgress)
            }
        }
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 30
            Text {
                anchors.fill: parent
                visible: dialog.controller.scanning
                text: "可继续操作已有视图。取消会保留已读取的序列。"
                color: Theme.textMuted
                font.pixelSize: 12
                wrapMode: Text.Wrap
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Components.AppButton {
                objectName: "importTaskRetry"
                text: "重试"
                visible: dialog.controller.importError && !dialog.controller.scanning
                compact: true
                onClicked: dialog.controller.retryImport()
            }
            Components.AppButton {
                objectName: "importTaskChoose"
                text: "重新选择…"
                visible: dialog.controller.importError && !dialog.controller.scanning
                compact: true
                onClicked: dialog.controller.openImportDialog()
            }
            Components.AppButton {
                objectName: "importTaskClose"
                text: dialog.controller.scanning ? "取消导入" : "关闭"
                compact: true
                onClicked: {
                    if (dialog.controller.scanning) dialog.controller.cancelImport()
                    else dialog.close()
                }
            }
        }
    }
}
