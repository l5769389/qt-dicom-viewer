pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"
ColumnLayout {
    id: root
    required property var settingsController
    spacing: 24
    Repeater {
        model: [{key: "gray", title: "CT / 普通灰阶影像"}, {key: "pet", title: "PET 影像"}]
        delegate: ColumnLayout {
            id: group
            required property var modelData
            Layout.fillWidth: true
            spacing: 12
            Text { text: group.modelData.title; color: Theme.textPrimary; font.pixelSize: 15; font.bold: true }
            GridLayout {
                Layout.fillWidth: true
                columns: root.width > 780 ? 3 : root.width > 390 ? 2 : 1
                columnSpacing: 10; rowSpacing: 10
                Repeater {
                    model: root.settingsController.colorMaps
                    delegate: Components.AppButton {
                        id: preset
                        required property var modelData
                        objectName: "colorMap-" + group.modelData.key + "-" + modelData.key
                        Layout.fillWidth: true
                        Layout.preferredHeight: 91
                        checkable: true
                        autoExclusive: true
                        checked: root.settingsController.values.colormap[group.modelData.key] === modelData.key
                        baseBorderWidth: 1
                        onClicked: root.settingsController.setValue("colormap", group.modelData.key, modelData.key)
                        contentItem: ColumnLayout {
                            spacing: 12
                            GradientStrip { Layout.fillWidth: true; colors: preset.modelData.colors }
                            RowLayout {
                                Text { Layout.fillWidth: true; text: preset.modelData.label; color: Theme.textPrimary; font.pixelSize: 13 }
                                Text { text: preset.checked ? "✓" : ""; color: Theme.primaryColor; font.pixelSize: 15 }
                            }
                        }
                    }
                }
            }
        }
    }
    Text { Layout.fillWidth: true; text: "应用于 2D、MPR 和 4D 灰阶影像；3D 使用各自的体绘制模板。"; color: Theme.textMuted; font.pixelSize: 12; wrapMode: Text.Wrap }
}
