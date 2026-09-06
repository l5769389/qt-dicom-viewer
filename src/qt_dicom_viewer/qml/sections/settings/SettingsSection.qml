import QtQuick
import QtQuick.Layouts
import "../../theme"

ColumnLayout {
    id: root
    default property alias contents: body.data
    property string title: ""
    property string description: ""
    spacing: 10
    data: [
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Text { text: root.title; color: Theme.textPrimary; font.pixelSize: 13; font.weight: Font.DemiBold }
            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.dividerColor }
        },
        Text {
            Layout.fillWidth: true
            visible: root.description !== ""
            text: root.description
            color: Theme.textMuted; font.pixelSize: 12; wrapMode: Text.Wrap
        },
        ColumnLayout {
            id: body
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            spacing: 6
        }
    ]
}
