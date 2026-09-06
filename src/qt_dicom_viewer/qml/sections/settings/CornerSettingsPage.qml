pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"
ColumnLayout {
    id: root
    required property var settingsController
    readonly property var values: settingsController.values.corners
    readonly property var fields: settingsController.cornerFields
    property string fieldSearch: ""
    readonly property var availableFields: fields.filter(item => (item.label + item.key).toLowerCase().indexOf(fieldSearch.toLowerCase()) >= 0)
    spacing: 12
    function fieldLabel(key) { return fields.find(item => item.key === key)?.label ?? key }
    SettingsCard {
        Layout.fillWidth: true
        Components.AppCheckBox { objectName: "setting-corners-enabled"; text: "显示四角信息"; checked: root.values.enabled; onClicked: root.settingsController.setValue("corners", "enabled", checked) }
        GridLayout {
            Layout.fillWidth: true
            columns: root.width > 650 ? 2 : 1
            columnSpacing: 16; rowSpacing: 10
            SettingSlider { Layout.fillWidth: true; title: "文字大小"; settingName: "corners-fontSize"; from: 10; to: 20; stepSize: 1; value: root.values.fontSize; onEdited: value => root.settingsController.setValue("corners", "fontSize", value) }
            SettingSlider { Layout.fillWidth: true; title: "行间距"; settingName: "corners-lineHeight"; from: 1; to: 1.8; stepSize: 0.1; suffix: " 倍"; value: root.values.lineHeight; onEdited: value => root.settingsController.setValue("corners", "lineHeight", value) }
            ColumnLayout {
                Layout.fillWidth: true
                Text { text: "文字颜色"; color: Theme.textSecondary; font.pixelSize: 12 }
                Components.AppComboBox {
                    objectName: "setting-corners-colorMode"
                    Layout.fillWidth: true
                    model: [{label: "自动对比背景", value: "auto"}, {label: "自定义颜色", value: "custom"}]
                    textRole: "label"; valueRole: "value"
                    currentIndex: root.values.colorMode === "auto" ? 0 : 1
                    onActivated: index => root.settingsController.setValue("corners", "colorMode", index === 0 ? "auto" : "custom")
                }
            }
            SettingColor { Layout.fillWidth: true; enabled: root.values.colorMode === "custom"; title: "自定义颜色"; settingName: "corners-color"; value: root.values.color; onEdited: color => root.settingsController.setValue("corners", "color", color) }
        }
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: Math.max(100, root.values.fontSize * root.values.lineHeight * 3 + 24)
            color: Theme.canvasBackground; radius: 5
            Text {
                anchors.left: parent.left; anchors.top: parent.top; anchors.margins: 12
                text: "CT · 轴位\n示例序列\nSlice: 8 / 16"
                font.pixelSize: root.values.fontSize; lineHeight: root.values.lineHeight
                color: root.values.colorMode === "custom" ? root.values.color : Theme.overlayText
            }
            Text {
                anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 12
                text: "Zoom: 125%\nWL: 40  WW: 400"
                horizontalAlignment: Text.AlignRight
                font.pixelSize: root.values.fontSize; lineHeight: root.values.lineHeight
                color: root.values.colorMode === "custom" ? root.values.color : Theme.overlayText
            }
        }
    }
    Text { text: "显示内容与顺序"; color: Theme.textPrimary; font.pixelSize: 14; font.bold: true }
    Components.AppTextField { objectName: "cornerFieldSearch"; Layout.fillWidth: true; placeholderText: "筛选可添加的信息项"; onTextEdited: root.fieldSearch = text }
    GridLayout {
        Layout.fillWidth: true
        columns: root.width > 730 ? 2 : 1
        columnSpacing: 12; rowSpacing: 12
        Repeater {
            model: [{key: "topLeft", title: "左上"}, {key: "topRight", title: "右上"}, {key: "bottomLeft", title: "左下"}, {key: "bottomRight", title: "右下"}]
            delegate: SettingsCard {
                id: corner
                required property var modelData
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                Text { text: corner.modelData.title + "  ·  " + root.values[corner.modelData.key].length + " / 8"; color: Theme.textPrimary; font.pixelSize: 14; font.bold: true }
                Repeater {
                    model: root.values[corner.modelData.key]
                    delegate: RowLayout {
                        id: entry
                        required property string modelData
                        required property int index
                        Layout.fillWidth: true
                        Text { Layout.fillWidth: true; text: root.fieldLabel(entry.modelData); color: Theme.textSecondary; font.pixelSize: 12; elide: Text.ElideRight }
                        Components.AppButton { objectName: "cornerUp-" + corner.modelData.key + "-" + entry.index; text: "↑"; compact: true; minimumButtonWidth: 28; enabled: entry.index > 0; onClicked: root.settingsController.moveCornerField(corner.modelData.key, entry.index, -1) }
                        Components.AppButton { objectName: "cornerDown-" + corner.modelData.key + "-" + entry.index; text: "↓"; compact: true; minimumButtonWidth: 28; enabled: entry.index < root.values[corner.modelData.key].length - 1; onClicked: root.settingsController.moveCornerField(corner.modelData.key, entry.index, 1) }
                        Components.AppButton { objectName: "cornerRemove-" + corner.modelData.key + "-" + entry.index; text: "×"; compact: true; minimumButtonWidth: 28; onClicked: root.settingsController.removeCornerField(corner.modelData.key, entry.index) }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Components.AppComboBox { id: choice; objectName: "cornerChoice-" + corner.modelData.key; Layout.fillWidth: true; model: root.availableFields; textRole: "label"; valueRole: "key" }
                    Components.AppButton { objectName: "cornerAdd-" + corner.modelData.key; text: "添加"; enabled: choice.currentIndex >= 0 && root.values[corner.modelData.key].length < 8; onClicked: root.settingsController.addCornerField(corner.modelData.key, choice.currentValue) }
                }
            }
        }
    }
}
