pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../components" as Components
import "../theme"

Components.AppDialog {
    id: dialog
    objectName: "exportDialog"
    property var controller: null
    property var settingsController: null
    parent: Basic.Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(560, parent ? parent.width - 32 : 560)
    height: Math.min(560, parent ? parent.height - 32 : 560)
    closeEnabled: !!controller && !controller.busy
    closeButtonName: "exportDialogClose"
    modal: true
    title: controller && controller.anonymousLocked ? "脱敏导出整个序列" : "导出序列"
    padding: 16
    onClosed: { if (controller) controller.closeDialog() }

    Connections {
        target: dialog.controller
        function onDialogChanged() {
            if (dialog.controller.dialogOpen) {
                format.currentIndex = 0
                anonymous.checked = true
                dialog.open()
            } else {
                dialog.close()
            }
        }
    }

    contentItem: Basic.ScrollView {
        id: exportScroll
        clip: true
        contentWidth: availableWidth
        Basic.ScrollBar.horizontal.policy: Basic.ScrollBar.AlwaysOff
        Basic.ScrollBar.vertical: Components.AppScrollBar {}
        ColumnLayout {
            width: exportScroll.availableWidth
            spacing: 14
            Text {
                Layout.fillWidth: true
                text: "整个序列 · " + (dialog.controller ? dialog.controller.instanceCount : 0) + " 个 DICOM 文件"
                color: Theme.textMuted
                font.pixelSize: 13
            }
            RowLayout {
                Layout.fillWidth: true
                Text { text: "导出格式"; color: Theme.textPrimary; font.pixelSize: 13 }
                Components.AppComboBox {
                    id: format
                    objectName: "exportFormat"
                    Layout.fillWidth: true
                    model: ["DICOM (.dcm)", "PNG (.png)"]
                    enabled: dialog.controller && !dialog.controller.busy
                }
            }
            Text {
                Layout.fillWidth: true
                text: format.currentIndex === 0 ? "保留原始像素与多帧结构。"
                    : "按影像窗宽 / 窗位及原始分辨率逐帧导出，不包含视口标注。"
                color: Theme.textMuted
                font.pixelSize: 12
                wrapMode: Text.Wrap
            }
            Components.AppCheckBox {
                id: anonymous
                objectName: "exportAnonymous"
                text: "匿名导出"
                checked: true
                enabled: dialog.controller && !dialog.controller.busy && !dialog.controller.anonymousLocked
            }
            Text {
                Layout.fillWidth: true
                text: anonymous.checked ? "清理身份元数据。像素内的文字不会被自动擦除，请确认影像不含身份信息。"
                    : format.currentIndex === 0 ? "保留源 DICOM 的全部信息，包括患者身份。"
                    : "PNG 文本元数据将包含患者姓名、ID 和检查 / 序列 UID。"
                color: Theme.textMuted
                wrapMode: Text.Wrap
                font.pixelSize: 12
            }
            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.dividerColor }
            Text { text: "导出位置"; color: Theme.textPrimary; font.pixelSize: 13 }
            Text {
                objectName: "exportDestination"
                Layout.fillWidth: true
                text: dialog.settingsController ? dialog.settingsController.exportDirectory : ""
                textFormat: Text.PlainText
                color: Theme.textMuted
                font.pixelSize: 12
                wrapMode: Text.WrapAnywhere
            }
            Components.AppButton {
                text: "更改导出位置…"
                normalColor: "transparent"
                baseBorderWidth: 1
                baseBorderColor: Theme.controlBorder
                compact: true
                enabled: dialog.controller && !dialog.controller.busy
                onClicked: dialog.settingsController.chooseExportDirectory()
            }
            Basic.ProgressBar {
                objectName: "exportProgress"
                Layout.fillWidth: true
                visible: dialog.controller && dialog.controller.busy
                from: 0
                to: dialog.controller ? Math.max(1, dialog.controller.totalCount) : 1
                value: dialog.controller ? dialog.controller.completedCount : 0
                indeterminate: dialog.controller && dialog.controller.totalCount === 0
            }
            Text {
                objectName: "exportMessage"
                Layout.fillWidth: true
                visible: text !== ""
                text: dialog.controller ? dialog.controller.message : ""
                textFormat: Text.PlainText
                color: Theme.textPrimary
                font.pixelSize: 13
                wrapMode: Text.Wrap
            }
            Text {
                objectName: "exportOutputDirectory"
                Layout.fillWidth: true
                visible: text !== ""
                text: dialog.controller ? dialog.controller.outputDirectory : ""
                textFormat: Text.PlainText
                color: Theme.textMuted
                font.pixelSize: 12
                wrapMode: Text.WrapAnywhere
            }

        }
    }
    footer: Components.AppDialogFooter {
        leading: Components.AppButton {
            objectName: "openExportOutput"
            text: "打开文件夹"
            visible: dialog.controller && dialog.controller.outputDirectory !== ""
            onClicked: dialog.controller.openOutputDirectory()
        }
        Components.AppButton {
            objectName: "cancelExport"
            text: dialog.controller && dialog.controller.busy ? "取消导出" : "取消"
            onClicked: {
                if (dialog.controller.busy) dialog.controller.cancelExport()
                else dialog.reject()
            }
        }
        Components.AppButton {
            objectName: "startExport"
            text: "开始导出"
            actionRole: "primary"
            enabled: dialog.controller && !dialog.controller.busy && dialog.controller.instanceCount > 0
            onClicked: dialog.controller.startExport(format.currentIndex === 0 ? "dicom" : "png", anonymous.checked)
        }
    }
}
