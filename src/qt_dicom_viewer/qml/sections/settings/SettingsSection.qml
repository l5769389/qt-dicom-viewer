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
        Text {
            Layout.fillWidth: true
            text: root.title; color: Theme.textPrimary
            font.pixelSize: 14; font.weight: Font.DemiBold
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
