pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../../components" as Components
import "../../../theme"

ColumnLayout {
    id: panel
    objectName: "zoomToolPanel"
    required property var viewportController
    readonly property real current: viewportController?.zoom ?? 1
    readonly property bool ready: !!viewportController
        && (viewportController.loadState === "ready" || (viewportController.sliceCount ?? 0) > 0)
    spacing: 8
    Text {
        Layout.fillWidth: true
        text: "当前缩放 " + Number(panel.current.toFixed(2)) + "×"
        color: Theme.textSecondary
        font.pixelSize: 12
    }
    GridLayout {
        Layout.fillWidth: true
        columns: 2
        columnSpacing: 6; rowSpacing: 6
        uniformCellWidths: true
        Repeater {
            model: [1, 2, 5, 10]
            delegate: Components.AppButton {
                required property int modelData
                objectName: "zoomShortcut-" + modelData
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                compact: true
                text: modelData + "×"
                enabled: panel.ready
                checked: Math.abs(panel.current - modelData) < 0.0001
                onClicked: panel.viewportController.setZoom(modelData)
            }
        }
    }
    Text {
        Layout.fillWidth: true
        text: "1× 为默认适配大小"
        color: Theme.textSubtle
        font.pixelSize: 11
        wrapMode: Text.Wrap
    }
}
