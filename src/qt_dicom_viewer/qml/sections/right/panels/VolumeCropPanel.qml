pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../../../theme"
import "../../../components" as Components
import "../components" as Controls

Item {
    id: root
    objectName: "volumeCropPanel"
    required property var viewportController
    readonly property var controller: viewportController && viewportController.viewportType === "volume" ? viewportController : null
    implicitHeight: controls.implicitHeight

    ColumnLayout {
        id: controls
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: 12

        Text {
            Layout.fillWidth: true
            text: "先选择裁剪方式，再按住左键圈选。松开鼠标后立即裁剪，范围沿当前视线贯穿影像。"
            wrapMode: Text.Wrap
            color: Theme.textSecondary
            font.pixelSize: 13
        }

        Repeater {
            model: [
                { mode: "inside", label: "内部裁剪", hint: "移除圈选区域内的影像" },
                { mode: "outside", label: "外部裁剪", hint: "保留圈选区域内的影像" }
            ]
            delegate: Components.AppButton {
                id: action
                required property var modelData
                objectName: "volumeCrop-" + modelData.mode
                Layout.fillWidth: true
                Layout.preferredHeight: 60
                enabled: !!root.controller && root.controller.loadState === "ready"
                    && !root.controller.editBusy
                checked: !!root.controller && root.controller.cropMode === modelData.mode
                Accessible.name: modelData.label
                onClicked: root.controller.setCropMode(modelData.mode)
                contentItem: Column {
                    spacing: 4
                    Text {
                        width: parent.width
                        text: action.modelData.label
                        color: action.enabled ? Theme.textPrimary : Theme.textDisabled
                        font.pixelSize: 14
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Text {
                        width: parent.width
                        text: action.modelData.hint
                        color: action.enabled ? Theme.textSecondary : Theme.textDisabled
                        font.pixelSize: 11
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
                baseBorderWidth: 1
                baseBorderColor: Theme.controlBorder
            }
        }

        Text {
            Layout.fillWidth: true
            text: root.controller && root.controller.hasCrop
                ? "已裁剪，可继续圈选。底部“重置裁剪”恢复全部裁剪，保留去床板状态。"
                : "默认内部裁剪。切换裁剪方式只影响下一次圈选。"
            wrapMode: Text.Wrap
            color: Theme.textSecondary
            font.pixelSize: 12
        }
    }
}
