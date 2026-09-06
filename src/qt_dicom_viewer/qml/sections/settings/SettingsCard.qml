import QtQuick
import QtQuick.Layouts
import "../../theme"
Rectangle {
    default property alias contents: content.data
    implicitHeight: content.implicitHeight + 32
    color: Theme.controlBackground
    border.color: Theme.borderDefault
    radius: 7
    ColumnLayout {
        id: content
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 16
        spacing: 16
    }
}
