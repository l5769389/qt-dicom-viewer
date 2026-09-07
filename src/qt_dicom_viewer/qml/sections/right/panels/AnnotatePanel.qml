pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../../theme"
import "../../../components" as Components
import "../components" as Controls

ColumnLayout {
    id: annotatePanel
    objectName: "annotatePanel"
    required property var viewportController
    readonly property var controller: annotatePanel.viewportController ? annotatePanel.viewportController.textAnnotationController : null
    spacing: 12

    RowLayout {
        Layout.fillWidth: true
        Controls.ToolActionButton {
            objectName: "annotateArrowMode"
            Layout.fillWidth: true
            compact: true
            momentary: true
            label: "箭头"
            iconName: "annotate"
            checked: annotatePanel.viewportController.activeInteraction === "annotate:arrow"
            onClicked: annotatePanel.viewportController.setAnnotationMode(false)
        }
        Controls.ToolActionButton {
            objectName: "annotateTextMode"
            Layout.fillWidth: true
            compact: true
            momentary: true
            label: "文字箭头"
            iconName: "annotate-text"
            checked: annotatePanel.viewportController.activeInteraction === "annotate:text"
            onClicked: annotatePanel.viewportController.setAnnotationMode(true)
        }
    }

    Text {
        Layout.fillWidth: true
        text: annotatePanel.viewportController.activeInteraction === "annotate:text" ? "拖动绘制文字箭头，单击箭身编辑。" : "拖动绘制箭头，选中后可移动或调整端点。"
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

    Basic.ScrollView {
        Layout.fillWidth: true
        Layout.minimumWidth: 0
        Layout.preferredHeight: 84
        contentWidth: availableWidth
        clip: true
        Basic.ScrollBar.vertical: Components.AppScrollBar {}
        Basic.ScrollBar.horizontal.policy: Basic.ScrollBar.AlwaysOff
        Basic.TextArea {
            id: annotationEditor
            objectName: "annotationTextEditor"
            text: annotatePanel.controller ? annotatePanel.controller.annotationText : ""
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
                if (activeFocus && annotatePanel.controller) {
                    annotatePanel.viewportController.setAnnotationMode(true);
                    annotatePanel.controller.setAnnotationText(text);
                }
            }

            background: Rectangle {
                color: Theme.controlBackground
                border.color: annotationEditor.activeFocus ? Theme.focusBorder : Theme.inputBorder
                radius: Theme.controlRadius
            }

            Connections {
                target: annotatePanel.controller
                function onEditorChanged() {
                    if (annotationEditor.text !== annotatePanel.controller.annotationText) {
                        annotationEditor.text = annotatePanel.controller.annotationText;
                    }
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

    Flow {
        Layout.fillWidth: true
        Layout.minimumWidth: 0
        spacing: 6

        Repeater {
            model: ["#ffd45c", "#66d0ff", "#7bd7a4", "#ef7777", "#f5f7fb", "#ff8a5b", "#c99cff"]

            delegate: Basic.Button {
                id: colorButton
                required property string modelData
                objectName: "annotationColor-" + modelData.slice(1)
                width: 28
                height: 28
                Accessible.name: "标注颜色 " + modelData
                checked: annotatePanel.controller && annotatePanel.controller.annotationColor === modelData
                onClicked: annotatePanel.controller?.setAnnotationColor(modelData)

                background: Rectangle {
                    radius: width / 2
                    color: colorButton.modelData
                    border.width: colorButton.checked ? 3 : 1
                    border.color: colorButton.checked ? Theme.selectionBorder : Theme.controlBorder
                }
            }
        }
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

        Components.AppSlider {
            id: fontSizeSlider
            objectName: "annotationFontSize"
            Layout.fillWidth: true
            from: 10
            to: 48
            stepSize: 1
            value: annotatePanel.controller ? annotatePanel.controller.annotationFontSize : 16
            onMoved: annotatePanel.controller?.setAnnotationFontSize(Math.round(value))
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
            model: annotatePanel.controller ? annotatePanel.controller.annotationItems : []

            delegate: Basic.Button {
                id: annotationItem
                required property var modelData
                objectName: "annotationListItem-" + modelData.annotationId
                Layout.fillWidth: true
                implicitHeight: 34
                checked: modelData.selected
                onClicked: annotatePanel.controller?.selectAnnotation(modelData.annotationId)

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
                    color: annotationItem.checked ? Theme.selectionBackground : Theme.controlBackground
                    border.color: annotationItem.checked ? Theme.selectionBorder : Theme.controlBorder
                    radius: Theme.controlRadius
                }
            }
        }

        Text {
            Layout.fillWidth: true
            visible: !annotatePanel.controller || annotatePanel.controller.annotationItems.length === 0
            text: "当前切片暂无标注"
            color: Theme.textDisabled
            font.pixelSize: 11
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 8

        Controls.ToolActionButton {
            objectName: "deleteSelectedAnnotation"
            Layout.fillWidth: true
            label: "删除选中标注"
            iconName: "delete"
            hoverColor: Theme.resetActionHover
            enabled: annotatePanel.controller?.hasSelection ?? false
            onClicked: annotatePanel.controller?.deleteSelected()
        }
        Controls.ToolActionButton {
            objectName: "clearAllAnnotations"
            Layout.fillWidth: true
            label: "清空当前切片标注"
            iconName: "clear"
            hoverColor: Theme.resetActionHover
            enabled: annotatePanel.controller?.hasAnnotations ?? false
            onClicked: annotatePanel.controller?.clearAll()
        }
    }

    Item {
        Layout.fillHeight: true
    }
}
