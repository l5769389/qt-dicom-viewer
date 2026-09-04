pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../../theme"

ColumnLayout {
    id: annotatePanel
    objectName: "annotatePanel"
    required property var viewportController
    readonly property var controller: annotatePanel.viewportController
        ? annotatePanel.viewportController.textAnnotationController
        : null
    spacing: 12

    Text {
        Layout.fillWidth: true
        text: "在影像上按住并拖拽绘制箭头；起点放置文字，箭头尖端指向目标。单击箭身可选中编辑。"
        color: Theme.textSubtle
        font.pixelSize: 11
        wrapMode: Text.Wrap
    }

    Text {
        text: "标注文字"
        color: Theme.textSecondary
        font.pixelSize: 12
        font.weight: Font.DemiBold
    }

    Basic.TextArea {
        id: annotationEditor
        objectName: "annotationTextEditor"
        Layout.fillWidth: true
        Layout.preferredHeight: 72
        text: annotatePanel.controller
            ? annotatePanel.controller.annotationText : ""
        color: Theme.textPrimary
        placeholderText: "请输入标注内容"
        placeholderTextColor: Theme.textDisabled
        wrapMode: TextEdit.Wrap
        selectByMouse: true
        font.pixelSize: 13
        leftPadding: 9
        rightPadding: 9
        topPadding: 7
        bottomPadding: 7

        onTextChanged: {
            if (activeFocus && annotatePanel.controller)
                annotatePanel.controller.setAnnotationText(text)
        }

        background: Rectangle {
            color: Theme.controlBackground
            border.color: annotationEditor.activeFocus
                ? Theme.focusBorder : Theme.controlBorder
            radius: 5
        }

        Connections {
            target: annotatePanel.controller
            function onEditorChanged() {
                if (annotationEditor.text
                        !== annotatePanel.controller.annotationText) {
                    annotationEditor.text = annotatePanel.controller.annotationText
                }
            }
        }
    }

    Text {
        text: "颜色"
        color: Theme.textSecondary
        font.pixelSize: 12
        font.weight: Font.DemiBold
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 7

        Repeater {
            model: [
                "#ffd45c", "#66d0ff", "#7bd7a4", "#ef7777",
                "#f5f7fb", "#ff8a5b", "#c99cff"
            ]

            delegate: Basic.Button {
                id: colorButton
                required property string modelData
                objectName: "annotationColor-" + modelData.slice(1)
                Layout.preferredWidth: 27
                Layout.preferredHeight: 27
                checked: annotatePanel.controller
                    && annotatePanel.controller.annotationColor === modelData
                onClicked: annotatePanel.controller?.setAnnotationColor(modelData)

                background: Rectangle {
                    radius: width / 2
                    color: colorButton.modelData
                    border.width: colorButton.checked ? 3 : 1
                    border.color: colorButton.checked
                        ? Theme.selectionBorder : Theme.controlBorder
                }
            }
        }
        Item { Layout.fillWidth: true }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 10

        Text {
            text: "字号"
            color: Theme.textSecondary
            font.pixelSize: 12
            font.weight: Font.DemiBold
        }

        Basic.Slider {
            id: fontSizeSlider
            objectName: "annotationFontSize"
            Layout.fillWidth: true
            from: 10
            to: 48
            stepSize: 1
            value: annotatePanel.controller
                ? annotatePanel.controller.annotationFontSize : 16
            onMoved: annotatePanel.controller?.setAnnotationFontSize(
                Math.round(value)
            )
        }

        Text {
            Layout.preferredWidth: 38
            horizontalAlignment: Text.AlignRight
            text: Math.round(fontSizeSlider.value) + " px"
            color: Theme.textPrimary
            font.pixelSize: 12
        }
    }

    Rectangle {
        Layout.fillWidth: true
        height: 1
        color: Theme.dividerColor
    }

    Text {
        text: "当前切片箭头标注"
        color: Theme.textSecondary
        font.pixelSize: 12
        font.weight: Font.DemiBold
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 5

        Repeater {
            model: annotatePanel.controller
                ? annotatePanel.controller.annotationItems : []

            delegate: Basic.Button {
                id: annotationItem
                required property var modelData
                objectName: "annotationListItem-" + modelData.annotationId
                Layout.fillWidth: true
                implicitHeight: 34
                checked: modelData.selected
                onClicked: annotatePanel.controller?.selectAnnotation(
                    modelData.annotationId
                )

                contentItem: RowLayout {
                    spacing: 8
                    Rectangle {
                        Layout.preferredWidth: 8
                        Layout.preferredHeight: 20
                        radius: 2
                        color: annotationItem.modelData.color
                    }
                    Text {
                        Layout.fillWidth: true
                        text: annotationItem.modelData.text
                        color: Theme.textPrimary
                        elide: Text.ElideRight
                        font.pixelSize: 12
                    }
                }
                background: Rectangle {
                    color: annotationItem.checked
                        ? Theme.selectionBackground : Theme.controlBackground
                    border.color: annotationItem.checked
                        ? Theme.selectionBorder : Theme.controlBorder
                    radius: 5
                }
            }
        }

        Text {
            Layout.fillWidth: true
            visible: !annotatePanel.controller
                || annotatePanel.controller.annotationItems.length === 0
            text: "当前切片暂无标注"
            color: Theme.textDisabled
            font.pixelSize: 11
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 8

        Basic.Button {
            id: deleteAnnotationButton
            objectName: "deleteSelectedAnnotation"
            Layout.fillWidth: true
            text: "删除选中"
            enabled: annotatePanel.controller?.hasSelection ?? false
            onClicked: annotatePanel.controller?.deleteSelected()
            contentItem: Text {
                text: deleteAnnotationButton.text
                color: deleteAnnotationButton.enabled
                    ? Theme.textSecondary : Theme.textDisabled
                font.pixelSize: 12
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            background: Rectangle {
                color: deleteAnnotationButton.hovered
                    ? Theme.controlHover : Theme.controlBackground
                border.color: Theme.controlBorder
                radius: 5
            }
        }

        Basic.Button {
            id: clearAnnotationsButton
            objectName: "clearAllAnnotations"
            Layout.fillWidth: true
            text: "清空全部"
            enabled: annotatePanel.controller?.hasAnnotations ?? false
            onClicked: annotatePanel.controller?.clearAll()
            contentItem: Text {
                text: clearAnnotationsButton.text
                color: clearAnnotationsButton.enabled
                    ? Theme.textSecondary : Theme.textDisabled
                font.pixelSize: 12
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            background: Rectangle {
                color: clearAnnotationsButton.hovered
                    ? Theme.controlHover : Theme.controlBackground
                border.color: Theme.controlBorder
                radius: 5
            }
        }
    }

    Item { Layout.fillHeight: true }
}
