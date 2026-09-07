import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"
import "SectionState.js" as State

Rectangle {
    id: root
    default property alias contents: body.data
    property string title: ""
    property string description: ""
    property string sectionKey: title
    property bool collapsed: false
    Component.onCompleted: collapsed = State.collapsed[sectionKey] === true
    implicitHeight: content.implicitHeight + 20
    color: Theme.panelBackground
    radius: 6
    ColumnLayout {
        id: content
        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
        anchors.margins: 10
        spacing: 8
        Components.AppButton {
            objectName: "settingsGroup-" + root.sectionKey
            Layout.fillWidth: true; Layout.preferredHeight: 28
            normalColor: "transparent"; compact: true
            Accessible.name: root.title + (root.collapsed ? "，展开" : "，收起")
            onClicked: { root.collapsed = !root.collapsed; State.collapsed[root.sectionKey] = root.collapsed }
            contentItem: RowLayout {
                Text { Layout.fillWidth: true; text: root.title; color: Theme.textPrimary; font.pixelSize: 14; font.weight: Font.DemiBold }
                Components.AppIcon { iconName: "chevron-down"; iconSize: 14; rotation: root.collapsed ? -90 : 0 }
            }
        }
        Text {
            Layout.fillWidth: true
            visible: !root.collapsed && root.description !== ""
            text: root.description; color: Theme.textMuted; font.pixelSize: 12; wrapMode: Text.Wrap
        }
        ColumnLayout {
            id: body
            visible: !root.collapsed
            Layout.fillWidth: true; Layout.minimumWidth: 0
            spacing: 6
        }
    }
}
