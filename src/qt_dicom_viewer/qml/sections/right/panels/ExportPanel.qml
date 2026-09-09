pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
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
    Components.AppCheckBox {
        id: anonymous
        objectName: "viewportExportAnonymous"
        text: "匿名导出"
        checked: true
        enabled: !!root.exportController && !root.exportController.busy
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        Components.AppButton {
            objectName: "exportPng"
            Layout.fillWidth: true
            text: "导出 PNG"
            normalColor: Theme.primaryButtonBackground
            hoverColor: Theme.primaryButtonHover
            pressedColor: Theme.primaryButtonPressed
            disabledColor: Theme.primaryButtonDisabled
            textColor: Theme.textOnPrimary
            compact: true
            enabled: !!root.exportController && !root.exportController.busy
            onClicked: root.exportController.exportPng(root.exportItem, Screen.devicePixelRatio, anonymous.checked)
        }
        Components.AppButton {
            objectName: "exportDicom"
            Layout.fillWidth: true
            text: "导出 DICOM"
            normalColor: "transparent"
            baseBorderWidth: 1
            baseBorderColor: Theme.primaryButtonBorder
            textColor: Theme.iconActive
            compact: true
            enabled: !!root.exportController && !root.exportController.busy
            onClicked: root.exportController.exportDicom(anonymous.checked)
        }
    }
    Text {
        Layout.fillWidth: true
        text: anonymous.checked
            ? "PNG · 当前视口，隐藏四角文字及文字标注\nDICOM · 清理身份标签，保留原始像素\n匿名不会擦除原始像素内的文字。"
            : "PNG · 当前视口与可见标注\nDICOM · 原始序列文件，保留像素与身份标签"
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
