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
    readonly property var settingsController: viewportController.settingsController
    readonly property var styleSettings: settingsController?.values.measurement ?? ({})
    readonly property bool textMode: viewportController.activeInteraction === "annotate:text"
    readonly property bool selectedArrow: (viewportController.measurementController?.measurementItems ?? []).some(
        item => item.type === "arrow" && item.measurementId === viewportController.measurementController.selectedMeasurementId)
    spacing: 12

    RowLayout {
        Layout.fillWidth: true
        Controls.ToolActionButton {
            objectName: "annotateArrowMode"
            Layout.fillWidth: true
            compact: true
            momentary: true
            label: "箭头"
            iconName: "annotate-arrow"
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
        text: (annotatePanel.textMode ? "拖动绘制文字箭头，单击箭身编辑。" : "拖动绘制箭头，选中后可移动或调整端点。")
            + "\n" + (Qt.platform.os === "osx" ? "⌘+C / ⌘+V" : "Ctrl+C / Ctrl+V") + " 复制 / 粘贴所选"
        color: Theme.textSubtle
        font.pixelSize: 11
        wrapMode: Text.Wrap
    }

    Text {
        visible: annotatePanel.textMode
        text: "标注文字"
        color: Theme.textSecondary
        font.pixelSize: 12
        font.weight: Font.DemiBold
    }

    Basic.ScrollView {
        visible: annotatePanel.textMode
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

    Row {
        id: colorPalette
        objectName: "annotationColors"
        readonly property real swatchSize: Math.max(24, Math.min(28, Math.floor((width - 6 * spacing) / 7)))
        Layout.fillWidth: true
        Layout.minimumWidth: 0
        spacing: 2

        Repeater {
            model: ["#ffd45c", "#66d0ff", "#7bd7a4", "#ef7777", "#f5f7fb", "#ff8a5b", "#c99cff"]

            delegate: Basic.Button {
                id: colorButton
                required property string modelData
                objectName: "annotationColor-" + modelData.slice(1)
                width: colorPalette.swatchSize
                height: width
                Accessible.name: "标注颜色 " + modelData
                checked: (annotatePanel.textMode
                    ? annotatePanel.controller?.annotationColor
                    : annotatePanel.styleSettings.annotationColor) === modelData
                onClicked: {
                    if (annotatePanel.textMode)
                        annotatePanel.controller?.setAnnotationColor(modelData)
                    else
                        annotatePanel.settingsController?.setValue("measurement", "annotationColor", modelData)
                }

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
        spacing: 8
        Text {
            text: "线宽"
            color: Theme.textSecondary
            font.pixelSize: 12
            font.weight: Font.DemiBold
        }
        Components.AppSlider {
            id: lineWidthSlider
            objectName: "annotationLineWidth"
            Layout.fillWidth: true
            from: 1
            to: 6
            stepSize: 0.5
            value: annotatePanel.styleSettings.lineWidth ?? 1.5
            Accessible.name: "标注线宽"
            onMoved: annotatePanel.settingsController?.setValue("measurement", "lineWidth", value)
        }
        Text {
            Layout.preferredWidth: 42
            horizontalAlignment: Text.AlignRight
            text: lineWidthSlider.value + " px"
            color: Theme.textPrimary
            font.pixelSize: 12
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        Text {
            text: "箭头大小"
            color: Theme.textSecondary
            font.pixelSize: 12
            font.weight: Font.DemiBold
        }
        Components.AppSlider {
            id: arrowSizeSlider
            objectName: "annotationArrowSize"
            Layout.fillWidth: true
            from: 8
            to: 28
            stepSize: 1
            value: annotatePanel.styleSettings.annotationSize ?? 14
            Accessible.name: "标注箭头大小"
            onMoved: annotatePanel.settingsController?.setValue("measurement", "annotationSize", Math.round(value))
        }
        Text {
            Layout.preferredWidth: 42
            horizontalAlignment: Text.AlignRight
            text: Math.round(arrowSizeSlider.value) + " px"
            color: Theme.textPrimary
            font.pixelSize: 12
        }
    }

    RowLayout {
        visible: annotatePanel.textMode
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

    Components.AppButton {
        objectName: "deleteSelectedAnnotation"
        Layout.fillWidth: true
        text: "删除所选"
        compact: true
        hoverColor: Theme.resetActionHover
        enabled: annotatePanel.textMode ? (annotatePanel.controller?.hasSelection ?? false) : annotatePanel.selectedArrow
        onClicked: annotatePanel.viewportController.deleteSelectedMeasurement()
    }

    Item { Layout.fillHeight: true }
}
