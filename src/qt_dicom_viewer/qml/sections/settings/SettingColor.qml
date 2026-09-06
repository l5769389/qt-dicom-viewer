pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"

ColumnLayout {
    id: root
    required property string title
    required property string value
    property string settingName: ""
    signal edited(string color)
    spacing: 6
    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        Text { Layout.fillWidth: true; Layout.minimumWidth: 40; text: root.title; color: Theme.textSecondary; font.pixelSize: 12; wrapMode: Text.Wrap }
        Rectangle { implicitWidth: 18; implicitHeight: 18; radius: 3; color: root.value; border.color: Theme.borderStrong }
        Components.AppTextField {
            objectName: "setting-" + root.settingName
            Layout.preferredWidth: 92
            text: root.value
            font.pixelSize: 12
            maximumLength: 7
            placeholderText: "#RRGGBB"
            Accessible.name: root.title
            onEditingFinished: { root.edited(text); text = Qt.binding(() => root.value) }
        }
    }
    Flow {
        Layout.fillWidth: true
        Layout.minimumWidth: 0
        spacing: 3
        Repeater {
            model: ["#f8fafc", "#182334", "#ffd45c", "#66d0ff", "#ef4444", "#22c55e", "#3b82f6", "#a855f7"]
            delegate: Components.AppButton {
                id: swatch
                required property string modelData
                width: 24; height: 24
                Accessible.name: root.title + " " + modelData
                checked: root.value === modelData
                onClicked: root.edited(modelData)
                background: Rectangle {
                    anchors.fill: parent
                    anchors.margins: 2
                    radius: 3
                    color: swatch.modelData
                    border.width: swatch.checked || swatch.activeFocus ? 2 : 1
                    border.color: swatch.checked || swatch.activeFocus ? Theme.focusBorder : Theme.borderStrong
                }
            }
        }
    }
}
