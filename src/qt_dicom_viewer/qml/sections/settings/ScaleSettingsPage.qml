pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "../center/viewportArea" as Views
import "../../theme"
ColumnLayout {
    id: root
    required property var settingsController
    readonly property var values: settingsController.values.scale
    SettingsCard {
        Layout.fillWidth: true
        Components.AppCheckBox { objectName: "setting-scale-enabled"; text: "显示比例尺"; checked: root.values.enabled; onClicked: root.settingsController.setValue("scale", "enabled", checked) }
        SettingColor { Layout.fillWidth: true; title: "比例尺颜色"; settingName: "scale-color"; value: root.values.color; onEdited: color => root.settingsController.setValue("scale", "color", color) }
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 180
            color: Theme.canvasBackground; radius: 5
            Views.ScaleBar { anchors.left: parent.left; anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; calibrated: true; pixelsPerMm: 2; options: root.values }
        }
        Text { Layout.fillWidth: true; text: "显示于 2D、MPR 和 4D 视图，长度随缩放自动调整。影像没有有效物理像素间距时隐藏比例尺。"; color: Theme.textMuted; font.pixelSize: 12; wrapMode: Text.Wrap }
    }
}
