pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../../../theme"

Item {
    id: root
    objectName: "volumeCropPanel"
    required property var viewportController
    readonly property var controller: viewportController && viewportController.viewportType === "volume"
        ? viewportController : null
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

        Repeater {
            model: [
                { mode: "inside", label: "裁剪内部", hint: "移除圈选区域内的影像" },
                { mode: "outside", label: "裁剪外部", hint: "移除圈选区域外的影像" }
            ]
            delegate: Basic.Button {
                id: action
                required property var modelData
                objectName: "volumeCrop-" + modelData.mode
                Layout.fillWidth: true
                Layout.preferredHeight: 60
                enabled: !!root.controller && root.controller.loadState === "ready"
                    && root.controller.hasCropSelection && !root.controller.editBusy
                Accessible.name: modelData.label
                onClicked: root.controller.applyCrop(modelData.mode)
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
                background: Rectangle {
                    radius: 6
                    color: action.down ? Theme.selectionBackground
                        : action.hovered && action.enabled ? Theme.controlHover : Theme.controlBackground
                    border.width: 1
                    border.color: Theme.controlBorder
                }
            }
        }

        Basic.Button {
            id: cancelButton
            objectName: "volumeCrop-clear"
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            text: "取消选区"
            enabled: !!root.controller && root.controller.hasCropSelection && !root.controller.editBusy
            onClicked: root.controller.clearCropSelection()
            contentItem: Text {
                text: cancelButton.text
                color: cancelButton.enabled ? Theme.textSecondary : Theme.textDisabled
                font.pixelSize: 12
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            background: Rectangle {
                radius: 6
                color: cancelButton.hovered && cancelButton.enabled ? Theme.controlHover : "transparent"
                border.width: 1
                border.color: Theme.controlBorder
            }
        }

        Text {
            Layout.fillWidth: true
            text: root.controller && root.controller.hasCrop
                ? "已裁剪，可继续圈选。底部“重置裁剪”恢复全部裁剪，保留去床板状态。"
                : "Esc 取消选区。旋转、缩放或改变视口大小后，请重新圈选。"
            wrapMode: Text.Wrap
            color: Theme.textSecondary
            font.pixelSize: 12
        }
    }
}
