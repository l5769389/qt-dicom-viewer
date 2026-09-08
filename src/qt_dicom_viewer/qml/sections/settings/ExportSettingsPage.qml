pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"

ColumnLayout {
    id: page
    required property var settingsController
    spacing: 12
    SettingsSection {
        Layout.fillWidth: true
        title: "导出位置"
        description: "所有导出自动保存到此位置，每次导出创建独立文件夹。"
        RowLayout {
            Layout.fillWidth: true
            Components.AppTextField {
                objectName: "exportDirectoryField"
                Layout.fillWidth: true
                text: page.settingsController.exportDirectory
                selectByMouse: true
                onEditingFinished: {
                    page.settingsController.setValue("export", "directory", text)
                    text = Qt.binding(function() { return page.settingsController.exportDirectory })
                }
            }
            Components.AppButton {
                objectName: "chooseExportDirectory"
                text: "选择目录…"
                onClicked: page.settingsController.chooseExportDirectory()
            }
        }
        Text {
            Layout.fillWidth: true
            text: "默认位置：" + page.settingsController.defaultExportDirectory
            textFormat: Text.PlainText
            color: Theme.textMuted
            wrapMode: Text.WrapAnywhere
            font.pixelSize: 12
        }
    }
    SettingsSection {
        Layout.fillWidth: true
        title: "格式与匿名"
        description: "导出时可选择 PNG 或 DICOM，每次默认启用匿名。"
        Text {
            Layout.fillWidth: true
            text: "PNG 按原始分辨率逐帧保存，使用影像内的窗宽 / 窗位；DICOM 保留原始像素。\n匿名会清理身份标签、私有标签及 UID，不会识别或擦除像素内的文字。"
            color: Theme.textMuted
            wrapMode: Text.Wrap
            font.pixelSize: 12
        }
    }
}
