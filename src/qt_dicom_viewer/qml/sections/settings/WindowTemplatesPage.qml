pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"
ColumnLayout {
    id: root
    required property var settingsController
    property string editingId: ""
    spacing: 24
    function clearEditor() { editingId = ""; name.text = ""; ww.text = "400"; wl.text = "40" }
    SettingsSection {
        Layout.fillWidth: true
        title: "可用模板"
        description: "勾选后显示在调窗面板中。自定义模板支持编辑和删除。"
        RowLayout {
            Layout.fillWidth: true; spacing: 12
            Text { Layout.fillWidth: true; text: "名称"; color: Theme.textSubtle; font.pixelSize: 11 }
            Text { Layout.minimumWidth: 78; Layout.maximumWidth: 78; Layout.fillWidth: true; objectName: "windowHeaderWW"; text: "窗宽 WW"; horizontalAlignment: Text.AlignRight; color: Theme.textSubtle; font.pixelSize: 11 }
            Text { Layout.minimumWidth: 78; Layout.maximumWidth: 78; Layout.fillWidth: true; objectName: "windowHeaderWL"; text: "窗位 WL"; horizontalAlignment: Text.AlignRight; color: Theme.textSubtle; font.pixelSize: 11 }
            Item { Layout.minimumWidth: 96; Layout.maximumWidth: 96; Layout.preferredHeight: 1 }
        }
        Repeater {
            model: root.settingsController.windowTemplates
            delegate: ColumnLayout {
                id: entry
                required property var modelData
                Layout.fillWidth: true; spacing: 2
                RowLayout {
                    Layout.fillWidth: true; spacing: 12
                    Components.AppCheckBox {
                        id: enabledBox
                        objectName: "windowEnabled-" + entry.modelData.presetId
                        Layout.fillWidth: true; Layout.minimumWidth: 72
                        text: entry.modelData.label
                        contentItem: Text {
                            text: enabledBox.text; textFormat: Text.PlainText
                            color: Theme.textSecondary; font.pixelSize: 13
                            verticalAlignment: Text.AlignVCenter
                            leftPadding: enabledBox.indicator.width + enabledBox.spacing
                            wrapMode: Text.Wrap
                        }
                        checked: entry.modelData.enabled
                        onClicked: root.settingsController.enableWindowTemplate(entry.modelData.presetId, checked)
                    }
                    Text { Layout.minimumWidth: 78; Layout.maximumWidth: 78; Layout.fillWidth: true; objectName: "windowWW-" + entry.modelData.presetId; text: entry.modelData.width; horizontalAlignment: Text.AlignRight; color: Theme.textSecondary; font.pixelSize: 12 }
                    Text { Layout.minimumWidth: 78; Layout.maximumWidth: 78; Layout.fillWidth: true; objectName: "windowWL-" + entry.modelData.presetId; text: entry.modelData.center; horizontalAlignment: Text.AlignRight; color: Theme.textSecondary; font.pixelSize: 12 }
                    RowLayout {
                        Layout.minimumWidth: 96; Layout.maximumWidth: 96; spacing: 4
                        Components.AppButton {
                            objectName: "windowEdit-" + entry.modelData.presetId
                            visible: !entry.modelData.builtin; text: "编辑"; compact: true
                            Layout.preferredWidth: 46; Layout.preferredHeight: 28
                            onClicked: { root.editingId = entry.modelData.presetId; name.text = entry.modelData.label; ww.text = entry.modelData.width; wl.text = entry.modelData.center }
                        }
                        Components.AppButton {
                            objectName: "windowDelete-" + entry.modelData.presetId
                            visible: !entry.modelData.builtin; text: "删除"; compact: true; actionRole: "danger"
                            Layout.preferredWidth: 46; Layout.preferredHeight: 28
                            onClicked: { root.settingsController.deleteWindowTemplate(entry.modelData.presetId); if (root.editingId === entry.modelData.presetId) root.clearEditor() }
                        }
                        Text { visible: entry.modelData.builtin; Layout.fillWidth: true; text: "系统"; horizontalAlignment: Text.AlignHCenter; color: Theme.textSubtle; font.pixelSize: 11 }
                    }
                }
                Rectangle { Layout.fillWidth: true; height: 1; color: Theme.borderSubtle }
            }
        }
    }
    SettingsSection {
        Layout.fillWidth: true
        title: root.editingId ? "编辑自定义模板" : "新增自定义模板"
        GridLayout {
            Layout.fillWidth: true
            columns: root.width >= 420 ? 3 : 1; columnSpacing: 12; rowSpacing: 10
            ColumnLayout {
                Layout.fillWidth: true
                Text { text: "名称"; color: Theme.textMuted; font.pixelSize: 11 }
                Components.AppTextField { id: name; objectName: "windowTemplateName"; Layout.fillWidth: true; placeholderText: "模板名称"; maximumLength: 40 }
            }
            ColumnLayout {
                Layout.fillWidth: true; Layout.minimumWidth: root.width >= 420 ? 100 : 0; Layout.maximumWidth: root.width >= 420 ? 100 : Infinity
                Text { text: "窗宽 WW"; color: Theme.textMuted; font.pixelSize: 11 }
                Components.AppTextField { id: ww; objectName: "windowTemplateWidth"; Layout.fillWidth: true; text: "400" }
            }
            ColumnLayout {
                Layout.fillWidth: true; Layout.minimumWidth: root.width >= 420 ? 100 : 0; Layout.maximumWidth: root.width >= 420 ? 100 : Infinity
                Text { text: "窗位 WL"; color: Theme.textMuted; font.pixelSize: 11 }
                Components.AppTextField { id: wl; objectName: "windowTemplateCenter"; Layout.fillWidth: true; text: "40" }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Text { text: root.settingsController.values.window.custom.length + " / 20"; color: Theme.textSubtle; font.pixelSize: 11 }
            Item { Layout.fillWidth: true }
            Components.AppButton {
                objectName: "cancelWindowTemplate"
                visible: !!root.editingId
                text: "取消"
                onClicked: root.clearEditor()
            }
            Components.AppButton {
                objectName: "saveWindowTemplate"
                actionRole: "primary"
                text: root.editingId ? "保存模板" : "添加模板"
                onClicked: {
                    if (root.settingsController.saveWindowTemplate(root.editingId, name.text, ww.text.trim() ? Number(ww.text) : NaN, wl.text.trim() ? Number(wl.text) : NaN)) root.clearEditor()
                }
            }
        }
    }
}
