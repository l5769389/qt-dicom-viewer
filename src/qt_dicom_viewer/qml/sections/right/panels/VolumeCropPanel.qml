pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../../../theme"
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
            text: "按住左键自由圈选，松开后闭合选区，再选择裁剪方式。裁剪沿当前视线贯穿影像。"
            wrapMode: Text.Wrap
            color: Theme.textSecondary
            font.pixelSize: 13
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Repeater {
                model: [
                    {
                        mode: "inside",
                        label: "裁剪内部 · 移除圈选区域内的影像"
                    },
                    {
                        mode: "outside",
                        label: "裁剪外部 · 移除圈选区域外的影像"
                    }
                ]
                delegate: Controls.ToolActionButton {
                    required property var modelData
                    objectName: "volumeCrop-" + modelData.mode
                    Layout.fillWidth: true
                    iconName: "crop-" + modelData.mode
                    label: modelData.label
                    enabled: !!root.controller && root.controller.loadState === "ready" && root.controller.hasCropSelection && !root.controller.editBusy
                    onClicked: root.controller.applyCrop(modelData.mode)
                }
            }
        }
        Controls.ToolActionButton {
            objectName: "volumeCrop-clear"
            Layout.fillWidth: true
            label: "取消选区"
            iconName: "clear"
            enabled: !!root.controller && root.controller.hasCropSelection && !root.controller.editBusy
            onClicked: root.controller.clearCropSelection()
        }

        Text {
            Layout.fillWidth: true
            text: root.controller && root.controller.hasCrop ? "已裁剪，可继续圈选。底部“重置裁剪”恢复全部裁剪，保留去床板状态。" : "Esc 取消选区。旋转、缩放或改变视口大小后，请重新圈选。"
            wrapMode: Text.Wrap
            color: Theme.textSecondary
            font.pixelSize: 12
        }
    }
}
