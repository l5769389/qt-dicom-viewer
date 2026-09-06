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
    spacing: 8
    Text { text: root.title; color: Theme.textSecondary; font.pixelSize: 12 }
    RowLayout {
        Layout.fillWidth: true
        Rectangle { implicitWidth: 30; implicitHeight: 30; radius: 5; color: root.value; border.color: Theme.borderStrong }
        Components.AppTextField {
            id: field
            objectName: "setting-" + root.settingName
            Layout.fillWidth: true
            text: root.value
            maximumLength: 7
            placeholderText: "#RRGGBB"
            onEditingFinished: { root.edited(text); text = Qt.binding(() => root.value) }
        }
    }
    Flow {
        Layout.fillWidth: true
        spacing: 5
        Repeater {
            model: ["#f8fafc", "#182334", "#ffd45c", "#66d0ff", "#ef4444", "#22c55e", "#3b82f6", "#a855f7"]
            delegate: Rectangle {
                id: swatch
                required property string modelData
                width: 23; height: 23; radius: 4
                color: modelData
                border.width: root.value === modelData ? 2 : 1
                border.color: root.value === modelData ? Theme.selectionBorder : Theme.borderStrong
                TapHandler { onTapped: root.edited(swatch.modelData) }
            }
        }
    }
}
