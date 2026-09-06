pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../../../theme"

ColumnLayout {
    id: panel
    objectName: "waterQaResults"
    property var controller: null
    readonly property var result: controller ? controller.currentResult : ({})
    readonly property bool ready: result.rois !== undefined
    spacing: 12

    component ActionButton: Basic.Button {
        id: action
        implicitHeight: 34
        contentItem: Text {
            text: action.text
            color: action.enabled ? Theme.textPrimary : Theme.textDisabled
            font.pixelSize: 12
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            radius: 5
            color: action.down ? Theme.selectionBackground
                : action.hovered ? Theme.controlHover : Theme.controlBackground
            border.width: 1
            border.color: Theme.controlBorder
        }
    }

    Text {
        Layout.fillWidth: true
        text: "水模 QA"
        color: Theme.textPrimary
        font.pixelSize: 14
        font.weight: Font.DemiBold
    }
    Text {
        objectName: "waterQaStatus"
        Layout.fillWidth: true
        text: panel.controller ? panel.controller.statusText : "请先加载 CT 影像"
        color: Theme.textSecondary
        wrapMode: Text.Wrap
        font.pixelSize: 12
    }

    Repeater {
        model: [
            { field: "roiDiameterMm", label: "VOI 直径 · mm", minimum: 2 },
            { field: "edgeClearanceMm", label: "距水模边缘 · mm", minimum: 0 }
        ]
        delegate: RowLayout {
            id: setting
            required property var modelData
            Layout.fillWidth: true
            spacing: 8
            Text {
                Layout.fillWidth: true
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
                    border.color: Theme.controlBorder
                }
            }
        }
    }

    ActionButton {
        objectName: "waterQa-analyze"
        Layout.fillWidth: true
        text: "自动识别"
        enabled: !!panel.controller && panel.controller.available && panel.controller.status !== "calculating"
        onClicked: panel.controller.analyze()
    }
    Text {
        objectName: "waterQaError"
        Layout.fillWidth: true
        visible: text.length > 0
        text: panel.controller ? panel.controller.error : ""
        color: "#f6bf66"
        wrapMode: Text.Wrap
        font.pixelSize: 12
    }
    Text {
        objectName: "waterQaPhantomSize"
        Layout.fillWidth: true
        visible: panel.ready
        text: panel.ready ? "水模直径约 " + Number(panel.result.phantom.radius_mm*2).toFixed(1)
            + " mm · 圆形 VOI × 5" : ""
        color: Theme.textMuted
        font.pixelSize: 11
        wrapMode: Text.Wrap
    }
    GridLayout {
        objectName: "waterQaMetrics"
        Layout.fillWidth: true
        visible: panel.ready
        columns: 2
        columnSpacing: 8
        rowSpacing: 10
        Repeater {
            model: panel.ready ? [
                {key: "water_ct_hu", label: "水 CT 值", hint: "中心 VOI 均值"},
                {key: "noise_hu", label: "噪声", hint: "中心 VOI 标准差"},
                {key: "uniformity_hu", label: "均匀性", hint: "四周相对中心最大绝对差"},
                {key: "consistency_range_hu", label: "区域一致性", hint: "5 个 VOI 均值极差"},
                {key: "horizontal_difference_hu", label: "横向差", hint: "左、右 VOI 均值绝对差"},
                {key: "vertical_difference_hu", label: "纵向差", hint: "上、下 VOI 均值绝对差"}
            ] : []
            delegate: ColumnLayout {
                id: metric
                required property var modelData
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                spacing: 4
                Text {
                    text: metric.modelData.label
                    color: Theme.textSecondary
                    font.pixelSize: 12
                }
                Text {
                    objectName: "waterQaMetric-" + metric.modelData.key
                    text: Number(panel.result[metric.modelData.key]).toFixed(2) + " HU"
                    color: Theme.textPrimary
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }
                Text {
                    Layout.fillWidth: true
                    text: metric.modelData.hint
                    color: Theme.textMuted
                    font.pixelSize: 10
                    wrapMode: Text.Wrap
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
            spacing: 4
            Repeater {
                model: ["VOI", "均值 / HU", "SD / HU", "Δ中心 / HU"]
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
                    model: [row.modelData.label, Number(row.modelData.mean_hu).toFixed(2),
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
    Text {
        Layout.fillWidth: true
        visible: panel.ready
        text: panel.ready ? "噪声极差  " + Number(panel.result.noise_range_hu).toFixed(2) + " HU\n"
            + "中心 VOI  " + panel.result.rois[0].pixel_count + " px · "
            + Number(panel.result.rois[0].area_mm2).toFixed(1) + " mm²" : ""
        color: Theme.textMuted
        font.pixelSize: 11
        wrapMode: Text.Wrap
    }
}
