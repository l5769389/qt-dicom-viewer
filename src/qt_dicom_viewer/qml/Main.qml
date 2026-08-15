import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "sections" as Sections

ApplicationWindow {
    id: window

    width: 1200
    height: 760
    visible: true
    title: "Qt DICOM Viewer"
    color: "#111419"

    RowLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        Sections.LeftPanel {
            Layout.preferredWidth: 220
            Layout.fillHeight: true
            panelController: appController.panelController
        }

        Sections.CenterPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            workspaceController: appController.workspaceController
        }

        Sections.RightPanel {
            Layout.preferredWidth: 260
            Layout.fillHeight: true
        }
    }
}
