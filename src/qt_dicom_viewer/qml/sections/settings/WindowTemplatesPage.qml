pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"
ColumnLayout {
    id: root
    required property var settingsController
    property string editingId: ""
    spacing: 12
    SettingsCard {
        Layout.fillWidth: true
        Text { text: "窗模板"; color: Theme.textPrimary; font.pixelSize: 14; font.bold: true }
        Text { Layout.fillWidth: true; text: "勾选的模板显示在调窗面板中。系统模板可以启停，自定义模板可以编辑和删除。"; color: Theme.textMuted; font.pixelSize: 12; wrapMode: Text.Wrap }
        Repeater {
            model: root.settingsController.windowTemplates
            delegate: RowLayout {
                id: entry
                required property var modelData
                Layout.fillWidth: true
                Components.AppCheckBox {
                    id: enabledBox
                    objectName: "windowEnabled-" + entry.modelData.presetId
                    Layout.fillWidth: true
                    Layout.minimumWidth: 72
                    text: entry.modelData.label
                    contentItem: Text {
                        text: enabledBox.text
                        textFormat: Text.PlainText
                        color: Theme.textSecondary
                        font.pixelSize: 13
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: enabledBox.indicator.width + enabledBox.spacing
                        elide: Text.ElideRight
                    }
                    checked: entry.modelData.enabled
                    onClicked: root.settingsController.enableWindowTemplate(entry.modelData.presetId, checked)
                }
                Text { text: "WW " + entry.modelData.width + "  /  WL " + entry.modelData.center; color: Theme.textMuted; font.pixelSize: 11 }
                Components.AppButton {
                    objectName: "windowEdit-" + entry.modelData.presetId
                    visible: !entry.modelData.builtin; text: "编辑"; compact: true
                    onClicked: { root.editingId = entry.modelData.presetId; name.text = entry.modelData.label; ww.text = entry.modelData.width; wl.text = entry.modelData.center }
                }
                Components.AppButton {
                    objectName: "windowDelete-" + entry.modelData.presetId
                    visible: !entry.modelData.builtin; text: "删除"; compact: true
                    onClicked: { root.settingsController.deleteWindowTemplate(entry.modelData.presetId); if (root.editingId === entry.modelData.presetId) root.editingId = "" }
                }
            }
        }
    }
    SettingsCard {
        Layout.fillWidth: true
        Text { text: root.editingId ? "编辑自定义模板" : "新增自定义模板"; color: Theme.textPrimary; font.pixelSize: 14; font.bold: true }
        Components.AppTextField { id: name; objectName: "windowTemplateName"; Layout.fillWidth: true; placeholderText: "模板名称"; maximumLength: 40 }
        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                Layout.fillWidth: true
                Text { text: "窗宽 WW"; color: Theme.textMuted; font.pixelSize: 12 }
                Components.AppTextField { id: ww; objectName: "windowTemplateWidth"; Layout.fillWidth: true; text: "400" }
            }
            ColumnLayout {
                Layout.fillWidth: true
                Text { text: "窗位 WL"; color: Theme.textMuted; font.pixelSize: 12 }
                Components.AppTextField { id: wl; objectName: "windowTemplateCenter"; Layout.fillWidth: true; text: "40" }
            }
        }
        RowLayout {
            Components.AppButton {
                objectName: "saveWindowTemplate"
                text: root.editingId ? "保存模板" : "添加模板"
                onClicked: {
                    if (root.settingsController.saveWindowTemplate(root.editingId, name.text, ww.text.trim() ? Number(ww.text) : NaN, wl.text.trim() ? Number(wl.text) : NaN)) {
                        root.editingId = ""; name.text = ""
                    }
                }
            }
            Components.AppButton { visible: !!root.editingId; text: "取消编辑"; onClicked: { root.editingId = ""; name.text = "" } }
            Item { Layout.fillWidth: true }
            Text { text: root.settingsController.values.window.custom.length + " / 20"; color: Theme.textSubtle; font.pixelSize: 11 }
        }
    }
}
