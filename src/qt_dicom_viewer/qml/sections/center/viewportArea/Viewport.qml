import QtQuick
import QtQuick.Layouts

Item {
    id: viewport
    required property var activeViewport
    required property bool hasTabs

    Rectangle {
        id: viewportArea
        anchors.fill: parent
        color: "#080a0d"
        clip: true

        DicomImage {
            anchors.fill: parent
            anchors.margins: 8
            activeViewport: viewport.activeViewport
        }

        Column {
            anchors.centerIn: parent
            spacing: 6
            visible: !hasTabs

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "No viewport open"
                color: "#778392"
                font.pixelSize: 16
                font.weight: Font.DemiBold
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Select a series from the left panel"
                color: "#505a67"
                font.pixelSize: 12
            }
        }

        Overlay {
            anchors.fill: parent
            anchors.margins: 8
            activeViewport: viewport.activeViewport

        }
    }
}