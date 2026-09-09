pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../../components" as Components
import "../../../theme"

ColumnLayout {
    id: panel
    objectName: "scrollToolPanel"
    required property var viewportController
    readonly property int count: viewportController?.sliceCount ?? 0
    readonly property int current: viewportController?.sliceIndex ?? -1
    spacing: 8
    Text {
        Layout.fillWidth: true
        text: panel.count > 0 ? "第 " + (panel.current + 1) + " / " + panel.count + " 页" : "当前视图不支持逐页浏览"
        color: Theme.textSecondary
        font.pixelSize: 12
        wrapMode: Text.Wrap
    }
    GridLayout {
        Layout.fillWidth: true
        columns: 2
        columnSpacing: 6; rowSpacing: 6
        uniformCellWidths: true
        Repeater {
            model: [{key:"first",label:"第一页",start:true}, {key:"last",label:"最后一页",start:false},
                    {key:"back10",label:"向前 10 页",start:true}, {key:"forward10",label:"向后 10 页",start:false}]
            delegate: Components.AppButton {
                required property var modelData
                objectName: "scrollShortcut-" + modelData.key
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                compact: true
                text: modelData.label
                enabled: panel.count > 1 && panel.current >= 0
                    && (modelData.start ? panel.current > 0 : panel.current < panel.count - 1)
                onClicked: {
                    const targets = {first:0, last:panel.count - 1, back10:panel.current - 10, forward10:panel.current + 10}
                    panel.viewportController.setSliceIndex(targets[modelData.key])
                }
            }
        }
    }
}
