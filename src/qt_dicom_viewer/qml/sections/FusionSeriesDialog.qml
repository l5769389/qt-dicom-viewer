pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../components" as Components
import "../theme"

Components.AppDialog {
    id: dialog
    objectName: "fusionSeriesDialog"
    required property var controller
    parent: Basic.Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(780, parent ? parent.width - 32 : 780)
    height: Math.min(640, parent ? parent.height - 32 : 640)
    padding: 16
    modal: true
    Basic.Overlay.modal: Rectangle { color: "#99000000" }
    title: "PET/CT 融合"
    titleIcon: "fusion"
    subtitle: "选择配对序列 · CT 固定层 / PET 移动层"

    function syncVisibility() {
        if (controller.fusionDialogOpen && !visible) open()
        else if (!controller.fusionDialogOpen && visible) close()
    }
    Component.onCompleted: syncVisibility()
    Connections {
        target: dialog.controller
        function onFusionDialogChanged() { dialog.syncVisibility() }
    }
    onClosed: {
        identityCheck.checked = false
        if (controller.fusionDialogOpen) controller.cancelFusion()
    }

    component SeriesPreview: Rectangle {
        id: preview
        required property var series
        implicitWidth: 80
        implicitHeight: 80
        color: Theme.canvasBackground
        radius: 5
        Image {
            id: thumbnail
            objectName: "fusionPreview-" + (preview.series.seriesUid || "")
            anchors.fill: parent
            anchors.margins: 3
            source: dialog.controller.fusionThumbnails[preview.series.seriesUid] || ""
            fillMode: Image.PreserveAspectFit
            smooth: true
        }
        Text {
            anchors.centerIn: parent
            visible: thumbnail.status !== Image.Ready
            text: "暂无预览"
            color: Theme.textSubtle
            font.pixelSize: 10
        }
    }

    component SeriesDetails: ColumnLayout {
        id: details
        required property var series
        spacing: 4
        Text {
            Layout.fillWidth: true
            text: details.series.description || "未命名序列"
            textFormat: Text.PlainText
            color: Theme.textPrimary
            font.pixelSize: 13
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }
        Text {
            Layout.fillWidth: true
            text: (details.series.patientName || "姓名未知") + " · "
                + (details.series.patientId || "ID 缺失")
            textFormat: Text.PlainText
            color: Theme.textSecondary
            font.pixelSize: 12
            elide: Text.ElideRight
        }
        Text {
            Layout.fillWidth: true
            text: (details.series.studyDate || "日期未知") + "  ·  " + (details.series.count || 0) + " 张"
            color: Theme.textMuted
            font.pixelSize: 11
            elide: Text.ElideRight
        }
        Text {
            Layout.fillWidth: true
            visible: text !== ""
            text: [details.series.relationship, details.series.spatialStatus].filter(Boolean).join(" · ")
            color: Theme.textMuted
            font.pixelSize: 11
            elide: Text.ElideRight
        }
        Text {
            Layout.fillWidth: true
            visible: text !== ""
            text: details.series.error || ""
            color: Theme.dangerColor
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }
    }

    contentItem: ColumnLayout {
        spacing: 10
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: Math.max(100, anchorRow.implicitHeight + 20)
            visible: !!dialog.controller.fusionAnchor.seriesUid
            color: Theme.cardBackground
            radius: 6
            RowLayout {
                id: anchorRow
                anchors.fill: parent
                anchors.margins: 10
                spacing: 12
                SeriesPreview { series: dialog.controller.fusionAnchor }
                SeriesDetails { Layout.fillWidth: true; series: dialog.controller.fusionAnchor }
                Text {
                    text: dialog.controller.fusionAnchor.modality === "CT" ? "CT · 固定层" : "PET · 移动层"
                    color: Theme.primaryHover
                    font.pixelSize: 12
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Text {
                text: dialog.controller.fusionAnchor.modality === "CT" ? "选择 PET 序列" : "选择 CT 序列"
                color: Theme.textPrimary
                font.pixelSize: 13
                font.weight: Font.DemiBold
            }
            Item { Layout.fillWidth: true }
            Text { text: "优先显示同患者、同检查"; color: Theme.textSubtle; font.pixelSize: 11 }
        }
        ListView {
            id: candidates
            objectName: "fusionCandidates"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 6
            model: dialog.controller.fusionCandidates
            Basic.ScrollBar.vertical: Components.AppScrollBar {}
            delegate: Basic.ItemDelegate {
                id: candidate
                required property var modelData
                objectName: "fusionCandidate-" + modelData.seriesUid
                width: candidates.width - 12
                height: Math.max(100, candidateRow.implicitHeight + 20)
                enabled: !modelData.error
                padding: 10
                hoverEnabled: true
                highlighted: dialog.controller.fusionPartnerUid === modelData.seriesUid
                onClicked: { identityCheck.checked = false; dialog.controller.selectFusionPartner(modelData.seriesUid) }
                background: Rectangle {
                    color: candidate.highlighted ? Theme.selectionBackground
                        : candidate.hovered ? Theme.controlHover : Theme.cardBackground
                    border.color: candidate.highlighted ? Theme.selectionBorder : Theme.borderSubtle
                    border.width: candidate.visualFocus ? 2 : 1
                    radius: 6
                }
                contentItem: RowLayout {
                    id: candidateRow
                    spacing: 12
                    SeriesPreview { series: candidate.modelData }
                    SeriesDetails { Layout.fillWidth: true; series: candidate.modelData }
                    Components.AppIcon {
                        iconName: "check"
                        iconSize: 20
                        iconColor: Theme.primaryColor
                        opacity: candidate.highlighted ? 1 : 0
                    }
                }
            }
            Text {
                anchors.centerIn: parent
                width: parent.width - 24
                visible: candidates.count === 0
                text: dialog.controller.fusionShowAllPatients ? "没有可配对的序列\n请先导入另一组 CT 或 PET 影像"
                    : "未找到同患者的 " + dialog.controller.fusionTargetModality + " 序列\n请导入对应影像，或展开人工配对"
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
                color: Theme.textMuted
                font.pixelSize: 12
            }
        }
        Components.AppCheckBox {
            objectName: "fusionShowAllPatients"
            Layout.fillWidth: true
            text: "显示其他患者 / 身份缺失的序列（人工配对）"
            checked: dialog.controller.fusionShowAllPatients
            onClicked: { identityCheck.checked = false; dialog.controller.setFusionShowAllPatients(checked) }
        }
        Text {
            Layout.fillWidth: true
            text: dialog.controller.fusionError
            visible: text !== ""
            color: Theme.dangerColor
            font.pixelSize: 12
            wrapMode: Text.Wrap
        }
        Text {
            Layout.fillWidth: true
            text: dialog.controller.fusionIdentityWarning
            visible: text !== ""
            color: Theme.textSecondary
            font.pixelSize: 12
            wrapMode: Text.Wrap
        }
        Components.AppCheckBox {
            id: identityCheck
            objectName: "fusionIdentityConfirmation"
            Layout.fillWidth: true
            visible: dialog.controller.fusionIdentityWarning !== ""
            text: "已核对两个来源，确认进行人工配对"
        }
    }
    footer: Components.AppDialogFooter {
        leading: Text {
            Layout.fillWidth: true
            text: "序列缩略图 · 配对后进入融合视图"
            color: Theme.textSubtle
            font.pixelSize: 11
            elide: Text.ElideRight
        }
        Components.AppButton {
            objectName: "cancelFusion"
            text: "取消"
            minimumButtonWidth: 80
            onClicked: dialog.controller.cancelFusion()
        }
        Components.AppButton {
            objectName: "confirmFusion"
            text: "融合浏览"
            iconName: "fusion"
            actionRole: "primary"
            minimumButtonWidth: 112
            enabled: dialog.controller.fusionCanConfirm
                && (dialog.controller.fusionIdentityWarning === "" || identityCheck.checked)
            onClicked: dialog.controller.confirmFusion(identityCheck.checked)
        }
    }
}
