pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../../theme"

ColumnLayout {
    id: panel
    objectName: "mtfResults"
    property var controller: null
    readonly property var result: controller ? controller.currentResult : ({})
    readonly property bool ready: result.x !== undefined && result.y !== undefined
    spacing: 14

    function metric(value, missing) {
        return value === null || value === undefined ? missing : Number(value).toFixed(3)
    }

    component SelectorButton: Basic.Button {
        id: selector
        required property string value
        required property string label
        property bool selected: false
        Layout.fillWidth: true
        Layout.preferredWidth: 1
        implicitHeight: 32
        contentItem: Text {
            text: selector.label
            color: selector.selected ? Theme.textPrimary : Theme.textSecondary
            font.pixelSize: 12
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            radius: 5
            color: selector.selected ? Theme.selectionBackground : Theme.controlBackground
            border.width: 1
            border.color: selector.selected ? Theme.selectionBorder : Theme.controlBorder
        }
    }

    Rectangle {
        Layout.fillWidth: true
        implicitHeight: 1
        color: Theme.dividerColor
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        Text {
            objectName: "mtfMeasurementMethodLabel"
            Layout.preferredWidth: 52
            text: "测量方法"
            color: Theme.textMuted
            font.pixelSize: 11
        }
        Repeater {
            model: panel.controller ? panel.controller.measurementMethods : []
            delegate: SelectorButton {
                required property var modelData
                objectName: "mtfMeasurementMethod-" + modelData.value
                value: modelData.value
                label: modelData.label
                selected: panel.controller?.measurementMethod === value
                onClicked: panel.controller?.setMeasurementMethod(value)
            }
        }
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        Text {
            objectName: "mtfAnalysisMethodLabel"
            Layout.preferredWidth: 52
            text: "分析方式"
            color: Theme.textMuted
            font.pixelSize: 11
        }
        Repeater {
            model: panel.controller ? panel.controller.analysisMethods : []
            delegate: SelectorButton {
                required property var modelData
                objectName: "mtfAnalysisMethod-" + modelData.value
                value: modelData.value
                label: modelData.label
                selected: panel.controller?.analysisMethod === value
                onClicked: panel.controller?.setAnalysisMethod(value)
            }
        }
    }
    Text {
        objectName: "mtfStatus"
        Layout.fillWidth: true
        visible: text.length > 0
        text: panel.controller ? panel.controller.statusText : "框选单颗微珠及外围背景"
        color: Theme.textSecondary
        font.pixelSize: 12
        wrapMode: Text.Wrap
    }
    Text {
        objectName: "mtfError"
        Layout.fillWidth: true
        visible: text.length > 0
        text: panel.controller ? panel.controller.error : ""
        color: "#f6bf66"
        font.pixelSize: 12
        wrapMode: Text.Wrap
    }
    MtfChart {
        Layout.fillWidth: true
        visible: panel.ready
        result: panel.result
    }
    GridLayout {
        objectName: "mtfMetrics"
        Layout.fillWidth: true
        visible: panel.ready
        columns: 4
        columnSpacing: 4
        rowSpacing: 12
        Text { text: "" }
        Repeater {
            model: ["MTF50\nlp/mm", "MTF10\nlp/mm", "FWHM\nLSF · mm"]
            Text {
                required property string modelData
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                text: modelData
                color: Theme.textMuted
                font.pixelSize: 11
                horizontalAlignment: Text.AlignHCenter
            }
        }
        Repeater {
            model: panel.ready ? [
                "X", panel.metric(panel.result.x.mtf50, "未达到"),
                panel.metric(panel.result.x.mtf10, "未达到"), panel.metric(panel.result.x.fwhm, "无法测量"),
                "Y", panel.metric(panel.result.y.mtf50, "未达到"),
                panel.metric(panel.result.y.mtf10, "未达到"), panel.metric(panel.result.y.fwhm, "无法测量")
            ] : []
            Text {
                required property string modelData
                required property int index
                objectName: "mtfMetric-" + index
                Layout.fillWidth: index % 4 !== 0
                Layout.preferredWidth: index % 4 === 0 ? 14 : 1
                text: modelData
                color: index < 4 ? "#41cce5" : "#f6bf66"
                font.pixelSize: 12
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
            }
        }
    }
    Repeater {
        model: panel.controller ? panel.controller.warnings : []
        Text {
            required property string modelData
            Layout.fillWidth: true
            text: "提示 · " + modelData
            color: "#f6bf66"
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }
    }
}
