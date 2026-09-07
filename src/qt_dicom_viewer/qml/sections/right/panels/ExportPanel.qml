pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../components" as Controls
import "../../../components" as Components
import "../../../theme"

ColumnLayout {
    id: root
    objectName: "exportPanel"
    property var exportController: null
    property Item exportItem: null
    spacing: 10
    Text {
        text: "导出"
        color: Theme.textPrimary
        font.pixelSize: 13
        font.weight: Font.DemiBold
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        Controls.ToolActionButton {
            objectName: "exportPng"
            Layout.fillWidth: true
            iconName: "export-png"
            label: "导出 PNG"
            enabled: !!root.exportController && !root.exportController.busy
            onClicked: root.exportController.exportPng(root.exportItem, Screen.devicePixelRatio)
        }
        Controls.ToolActionButton {
            objectName: "exportDicom"
            Layout.fillWidth: true
            iconName: "export-dicom"
            label: "导出 DICOM"
            enabled: !!root.exportController && !root.exportController.busy
            onClicked: root.exportController.exportDicom()
        }
    }
    Text {
        Layout.fillWidth: true
        text: "PNG · 当前视口与可见标注\nDICOM · 原始序列文件，保留像素与标签"
        color: Theme.textMuted
        font.pixelSize: 11
        wrapMode: Text.Wrap
        lineHeight: 1.4
    }
    Basic.ProgressBar {
        Layout.fillWidth: true
        visible: !!root.exportController && root.exportController.busy
        value: root.exportController ? root.exportController.progress : 0
        indeterminate: value === 0
    }
    Text {
        objectName: "exportMessage"
        Layout.fillWidth: true
        text: root.exportController ? root.exportController.message : ""
        visible: text !== ""
        wrapMode: Text.WrapAnywhere
        font.pixelSize: 12
        color: root.exportController && root.exportController.isError ? Theme.dangerColor : Theme.textSecondary
    }
    Components.AppButton {
        text: "取消导出"
        visible: !!root.exportController && root.exportController.busy
        onClicked: root.exportController.cancel()
    }
}
