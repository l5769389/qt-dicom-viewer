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

    function showInfo(anchor, title, detail) {
        info.title = title
        info.detail = detail
        info.open()
        info.origin = anchor.mapToItem(info.parent, 0, anchor.height + 6)
    }

    component InfoButton: Basic.Button {
        id: help
        required property string infoKey
        required property string title
        required property string detail
        objectName: "waterQaInfo-" + infoKey
        implicitWidth: 22
        implicitHeight: 22
        padding: 3
        Accessible.name: title + "说明"
        contentItem: Text {
            text: "i"
            color: help.hovered ? Theme.textPrimary : Theme.textMuted
            font.pixelSize: 11
            font.italic: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            anchors.centerIn: parent
            width: 14; height: 14
            radius: 7
            color: help.down ? Theme.selectionBackground : "transparent"
            border.color: help.hovered ? Theme.textPrimary : Theme.textMuted
        }
        onClicked: panel.showInfo(help, title, detail)
    }

    Basic.Popup {
        id: info
        objectName: "waterQaInfoPopup"
        parent: Basic.Overlay.overlay
        property string title: ""
        property string detail: ""
        property point origin: Qt.point(12, 12)
        width: Math.min(288, parent ? parent.width - 24 : 288)
        x: Math.max(12, Math.min(origin.x, (parent ? parent.width : 0) - width - 12))
        y: Math.max(12, Math.min(origin.y, (parent ? parent.height : 0) - height - 12))
        padding: 14
        focus: true
        closePolicy: Basic.Popup.CloseOnEscape | Basic.Popup.CloseOnPressOutside
        background: Rectangle {
            radius: 8
            color: Theme.panelBackgroundStrong
            border.color: Theme.controlBorder
        }
        contentItem: ColumnLayout {
            spacing: 8
            RowLayout {
                Layout.fillWidth: true
                Text {
                    Layout.fillWidth: true
                    text: info.title
                    color: Theme.textPrimary
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                }
                Basic.Button {
                    objectName: "waterQaInfoClose"
                    implicitWidth: 24; implicitHeight: 24
                    Accessible.name: "关闭说明"
                    contentItem: Text {
                        text: "×"
                        color: Theme.textSecondary
                        font.pixelSize: 18
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Item {}
                    onClicked: info.close()
                }
            }
            Text {
                objectName: "waterQaInfoDetail"
                Layout.fillWidth: true
                text: info.detail
                color: Theme.textSecondary
                wrapMode: Text.Wrap
                font.pixelSize: 12
                lineHeight: 1.3
            }
        }
    }

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
        Text {
            objectName: "waterQaPhantomSize"
            visible: panel.ready
            text: panel.ready ? "Ø " + Number(panel.result.phantom.radius_mm*2).toFixed(1) + " mm" : ""
            color: Theme.textMuted
            font.pixelSize: 11
        }
        InfoButton {
            infoKey: "overview"
            title: "水模 QA"
            detail: "自动定位当前 CT 切片的水模，放置中心、左、右、上、下 5 个圆形 ROI。\n\n在水模 QA 工具中拖动圆内区域，松开后更新指标；Esc 取消本次拖动。ROI 需位于水模内且互不重叠。\n\n重新识别恢复自动位置，底部重置清除 QA。仅显示实测值。"
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
            { field: "roiDiameterMm", label: "ROI 直径 · mm", minimum: 2,
                hint: "5 个圆形 ROI 使用相同的物理直径。修改后恢复自动布局并重新计算。"},
            { field: "edgeClearanceMm", label: "自动边距 · mm", minimum: 0,
                hint: "自动布局时，四周 ROI 外缘到水模边缘的距离。手动拖动不受此边距限制。修改后恢复自动布局。"}
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
            InfoButton {
                infoKey: setting.modelData.field
                title: setting.modelData.label
                detail: setting.modelData.hint
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
                {key: "water_ct_hu", label: "水 CT 值", hint: "中心 ROI 的平均 CT 值。使用原始 HU 像素计算，不受窗宽、窗位或显示变换影响。"},
                {key: "noise_hu", label: "噪声", hint: "中心 ROI 内像素的总体标准差（SD），单位 HU。"},
                {key: "uniformity_hu", label: "均匀性", hint: "四周 ROI 均值与中心 ROI 均值之差的最大绝对值，单位 HU。"},
                {key: "consistency_range_hu", label: "一致性", hint: "5 个 ROI 均值的极差：最大均值 − 最小均值，单位 HU。"},
                {key: "horizontal_difference_hu", label: "横向差", hint: "左、右 ROI 均值之差的绝对值，单位 HU。手动调整后仍按原标签计算。"},
                {key: "vertical_difference_hu", label: "纵向差", hint: "上、下 ROI 均值之差的绝对值，单位 HU。手动调整后仍按原标签计算。"}
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
                    InfoButton {
                        infoKey: metric.modelData.key
                        title: metric.modelData.label
                        detail: metric.modelData.hint
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
            InfoButton {
                infoKey: "statistics"
                title: "ROI 统计"
                detail: "均值：ROI 内像素的平均 CT 值。\nSD：总体标准差。\nΔ中心：当前 ROI 均值 − 中心 ROI 均值。\n\n"
                    + (panel.ready && !panel.editing ? "噪声极差：" + Number(panel.result.noise_range_hu).toFixed(2) + " HU\n"
                        + "中心采样：" + panel.result.rois[0].pixel_count + " px · "
                        + Number(panel.result.rois[0].area_mm2).toFixed(1) + " mm²" : "")
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
