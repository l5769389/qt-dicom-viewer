pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../../../theme"
import "../../../components" as Components

ColumnLayout {
    id: panel
    objectName: "waterQaResults"
    property var controller: null
    readonly property var result: controller ? controller.currentResult : ({})
    readonly property bool ready: result.rois !== undefined
    readonly property bool editing: controller ? controller.dragging : false
    spacing: 10

    signal manualRequested()

    component ActionButton: Components.AppButton {
        compact: true
        momentary: true
        fontPixelSize: 12
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 4
        Text {
            Layout.fillWidth: true
            text: "水模 QA"
            color: Theme.textPrimary
            font.pixelSize: 14
            font.weight: Font.DemiBold
        }
        Components.ToolbarAction {
            buttonObjectName: "waterQaManualButton"
            Layout.preferredWidth: 26
            Layout.preferredHeight: 26
            label: "水模 QA 操作手册"
            iconName: "manual"
            iconSize: 18
            onTriggered: panel.manualRequested()
        }
        Text {
            objectName: "waterQaPhantomSize"
            visible: panel.ready
            text: panel.ready ? "Ø " + Number(panel.result.phantom.radius_mm*2).toFixed(1) + " mm" : ""
            color: Theme.textMuted
            font.pixelSize: 11
        }
    }
    Text {
        objectName: "waterQaStatus"
        Layout.fillWidth: true
        text: panel.controller ? panel.controller.statusText : "请先加载 CT 影像"
        visible: text.length > 0
        color: Theme.textSecondary
        wrapMode: Text.Wrap
        font.pixelSize: 12
    }

    Repeater {
        model: [
            { field: "roiDiameterMm", label: "ROI 直径 · mm", minimum: 2},
            { field: "edgeClearanceMm", label: "自动边距 · mm", minimum: 0}
        ]
        delegate: RowLayout {
            id: setting
            required property var modelData
            Layout.fillWidth: true
            spacing: 8
            Text {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                wrapMode: Text.Wrap
                text: setting.modelData.label
                color: Theme.textSecondary
                font.pixelSize: 12
            }
            Basic.SpinBox {
                id: number
                objectName: "waterQaSetting-" + setting.modelData.field
                Layout.preferredWidth: 92
                implicitHeight: 30
                from: setting.modelData.minimum
                to: 100
                value: panel.controller ? panel.controller[setting.modelData.field] : 20
                enabled: !!panel.controller && panel.controller.available
                editable: true
                leftPadding: 24
                rightPadding: 24
                onValueModified: {
                    if (setting.modelData.field === "roiDiameterMm")
                        panel.controller.setRoiDiameterMm(value)
                    else
                        panel.controller.setEdgeClearanceMm(value)
                }
                contentItem: TextInput {
                    text: number.textFromValue(number.value, number.locale)
                    color: number.enabled ? Theme.textPrimary : Theme.textDisabled
                    font.pixelSize: 12
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    readOnly: !number.editable
                    validator: number.validator
                    inputMethodHints: Qt.ImhDigitsOnly
                    selectByMouse: true
                }
                up.indicator: Rectangle {
                    x: number.width-width
                    width: 22; height: number.height
                    color: number.up.pressed ? Theme.selectionBackground : "transparent"
                    Text { anchors.centerIn: parent; text: "+"; color: Theme.textSecondary }
                }
                down.indicator: Rectangle {
                    width: 22; height: number.height
                    color: number.down.pressed ? Theme.selectionBackground : "transparent"
                    Text { anchors.centerIn: parent; text: "−"; color: Theme.textSecondary }
                }
                background: Rectangle {
                    radius: 5
                    color: Theme.controlBackground
                    border.width: 1
                    border.color: number.visualFocus ? Theme.focusBorder : Theme.inputBorder
                }
            }
        }
    }

    ActionButton {
        objectName: "waterQa-analyze"
        Layout.fillWidth: true
        text: panel.ready ? "重新识别" : "自动识别"
        enabled: !!panel.controller && panel.controller.available && panel.controller.status !== "calculating"
        onClicked: panel.controller.analyze()
    }
    Text {
        objectName: "waterQaError"
        Layout.fillWidth: true
        visible: text.length > 0
        text: panel.controller ? panel.controller.error : ""
        color: Theme.warningColor
        wrapMode: Text.Wrap
        font.pixelSize: 12
    }
    GridLayout {
        objectName: "waterQaMetrics"
        Layout.fillWidth: true
        visible: panel.ready
        columns: 2
        uniformCellWidths: true
        columnSpacing: 8
        rowSpacing: 10
        Repeater {
            model: panel.ready ? [
                {key: "water_ct_hu", label: "水 CT 值"},
                {key: "noise_hu", label: "噪声"},
                {key: "uniformity_hu", label: "均匀性"},
                {key: "consistency_range_hu", label: "一致性"},
                {key: "horizontal_difference_hu", label: "横向差"},
                {key: "vertical_difference_hu", label: "纵向差"}
            ] : []
            delegate: ColumnLayout {
                id: metric
                required property var modelData
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                spacing: 4
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Text {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        wrapMode: Text.Wrap
                        text: metric.modelData.label
                        color: Theme.textSecondary
                        font.pixelSize: 12
                    }
                    Item { Layout.fillWidth: true }
                }
                Text {
                    Layout.fillWidth: true
                    objectName: "waterQaMetric-" + metric.modelData.key
                    text: panel.editing ? "—" : Number(panel.result[metric.modelData.key]).toFixed(2) + " HU"
                    color: Theme.textPrimary
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }
            }
        }
    }

    ColumnLayout {
        objectName: "waterQaRoiTable"
        Layout.fillWidth: true
        visible: panel.ready
        spacing: 8
        RowLayout {
            Layout.fillWidth: true
            spacing: 2
            Text {
                text: "ROI 统计"
                color: Theme.textSecondary
                font.pixelSize: 12
            }
            Item { Layout.fillWidth: true }
            Text { text: "HU"; color: Theme.textMuted; font.pixelSize: 10 }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 4
            Repeater {
                model: ["ROI", "均值", "SD", "Δ中心"]
                Text {
                    required property string modelData
                    Layout.fillWidth: true
                    Layout.preferredWidth: 1
                    text: modelData
                    color: Theme.textMuted
                    font.pixelSize: 10
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
        Repeater {
            model: panel.ready ? panel.result.rois : []
            delegate: RowLayout {
                id: row
                required property var modelData
                objectName: "waterQaRow-" + modelData.key
                Layout.fillWidth: true
                spacing: 4
                Repeater {
                    model: panel.editing ? [row.modelData.label, "—", "—", "—"]
                        : [row.modelData.label, Number(row.modelData.mean_hu).toFixed(2),
                        Number(row.modelData.std_hu).toFixed(2), Number(row.modelData.delta_center_hu).toFixed(2)]
                    Text {
                        required property string modelData
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        text: modelData
                        color: Theme.textSecondary
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }
        }
    }
}
