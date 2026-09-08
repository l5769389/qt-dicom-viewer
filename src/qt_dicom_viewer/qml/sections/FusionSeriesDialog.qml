pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../components" as Components
import "../theme"

Basic.Dialog {
    id: dialog
    objectName: "fusionSeriesDialog"
    required property var controller
    readonly property var anchorSeries: controller.fusionAnchor
    parent: Basic.Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(680, parent ? parent.width - 32 : 680)
    height: Math.min(implicitHeight, parent ? parent.height - 32 : 630)
    padding: 20
    modal: true
    title: "PET/CT 融合浏览"
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
    background: Rectangle { color: Theme.panelBackground; border.color: Theme.borderStrong; radius: 12 }
    header: Item {
        implicitHeight: 64
        Column {
            anchors.left: parent.left; anchors.leftMargin: 20
            anchors.verticalCenter: parent.verticalCenter
            spacing: 5
            Text { text: dialog.title; color: Theme.textPrimary; font.pixelSize: 18; font.bold: true }
            Text { text: "选择互补序列，在同一位置联动查看 CT、PET、融合与 MIP"; color: Theme.textMuted; font.pixelSize: 12 }
        }
    }
    contentItem: ColumnLayout {
        spacing: 12
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 86
            color: Theme.cardBackground
            radius: 8
            border.color: Theme.borderSubtle
            RowLayout {
                anchors.fill: parent; anchors.margins: 12; spacing: 12
                Text { text: dialog.anchorSeries.modality ?? "—"; color: Theme.primaryColor; font.pixelSize: 18; font.bold: true }
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 4
                    Text { text: "已选序列"; color: Theme.textMuted; font.pixelSize: 11 }
                    Text {
                        Layout.fillWidth: true
                        text: dialog.anchorSeries.description ?? "请先选择 CT 或 PET 序列"
                        textFormat: Text.PlainText
                        elide: Text.ElideRight; color: Theme.textPrimary; font.pixelSize: 13; font.bold: true
                    }
                    Text {
                        Layout.fillWidth: true
                        text: [dialog.anchorSeries.patientName, dialog.anchorSeries.patientId,
                               dialog.anchorSeries.studyDate].filter(Boolean).join(" · ")
                        textFormat: Text.PlainText
                        elide: Text.ElideRight; color: Theme.textMuted; font.pixelSize: 11
                    }
                }
                Text { text: (dialog.anchorSeries.count ?? 0) + " 张"; color: Theme.textMuted; font.pixelSize: 12 }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Text { text: "选择 " + dialog.controller.fusionTargetModality + " 序列"; color: Theme.textPrimary; font.bold: true }
            Item { Layout.fillWidth: true }
            Text { text: candidates.count + " 个候选"; color: Theme.textMuted; font.pixelSize: 12 }
        }
        ListView {
            id: candidates
            objectName: "fusionCandidates"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredHeight: Math.max(1, Math.min(3, count)) * 96
            clip: true
            spacing: 8
            model: dialog.controller.fusionCandidates
            Basic.ScrollBar.vertical: Basic.ScrollBar {}
            delegate: Basic.ItemDelegate {
                id: candidate
                required property var modelData
                objectName: "fusionCandidate-" + modelData.seriesUid
                width: candidates.width - 12
                height: 88
                enabled: !modelData.error
                highlighted: dialog.controller.fusionPartnerUid === modelData.seriesUid
                onClicked: { identityCheck.checked = false; dialog.controller.selectFusionPartner(modelData.seriesUid) }
                background: Rectangle {
                    color: candidate.highlighted ? Theme.selectionBackground : candidate.hovered ? Theme.cardBackgroundHover : Theme.cardBackground
                    border.color: candidate.highlighted ? Theme.primaryColor : Theme.borderSubtle
                    radius: 8
                }
                contentItem: RowLayout {
                    spacing: 12
                    Rectangle {
                        Layout.preferredWidth: 50; Layout.preferredHeight: 58
                        color: Theme.canvasBackground; radius: 6
                        Image { anchors.fill: parent; anchors.margins: 3; source: candidate.modelData.thumbnailUrl; fillMode: Image.PreserveAspectFit }
                        Text { anchors.centerIn: parent; visible: !candidate.modelData.thumbnailUrl; text: candidate.modelData.modality; color: Theme.textMuted }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true; spacing: 5
                        Text {
                            Layout.fillWidth: true
                            text: candidate.modelData.description + " · " + candidate.modelData.count + " 张"
                            textFormat: Text.PlainText
                            color: candidate.enabled ? Theme.textPrimary : Theme.textDisabled
                            elide: Text.ElideRight; font.pixelSize: 13; font.bold: true
                        }
                        Text {
                            Layout.fillWidth: true
                            text: [candidate.modelData.patientName, candidate.modelData.patientId, candidate.modelData.studyDate].filter(Boolean).join(" · ")
                            textFormat: Text.PlainText
                            color: Theme.textMuted; elide: Text.ElideRight; font.pixelSize: 11
                        }
                        Text {
                            Layout.fillWidth: true
                            text: candidate.modelData.error || candidate.modelData.relationship + "  /  " + candidate.modelData.spatialStatus
                            textFormat: Text.PlainText
                            color: candidate.modelData.error ? Theme.dangerColor : Theme.textSecondary
                            elide: Text.ElideRight; font.pixelSize: 11
                        }
                    }
                    Text { text: candidate.highlighted ? "✓" : ""; color: Theme.primaryColor; font.pixelSize: 20 }
                }
            }
            Text {
                anchors.centerIn: parent
                width: parent.width - 24
                visible: candidates.count === 0
                text: dialog.controller.fusionShowAllPatients
                    ? "没有可配对的 " + dialog.controller.fusionTargetModality + " 序列，请先导入影像。"
                    : "未找到同患者的 " + dialog.controller.fusionTargetModality + " 序列。\n可导入对应影像，或展开其他患者进行人工配对。"
                color: Theme.textMuted; wrapMode: Text.Wrap; horizontalAlignment: Text.AlignHCenter
            }
        }
        Components.AppCheckBox {
            objectName: "fusionShowAllPatients"
            Layout.fillWidth: true
            text: "显示其他患者 / 身份缺失的序列（人工配对）"
            checked: dialog.controller.fusionShowAllPatients
            onClicked: { identityCheck.checked = false; dialog.controller.setFusionShowAllPatients(checked) }
        }
        Text { Layout.fillWidth: true; text: dialog.controller.fusionError; visible: text !== ""; color: Theme.dangerColor; wrapMode: Text.Wrap; font.pixelSize: 12 }
        Text { Layout.fillWidth: true; text: dialog.controller.fusionIdentityWarning; visible: text !== ""; color: Theme.warningColor; wrapMode: Text.Wrap; font.pixelSize: 12; textFormat: Text.PlainText }
        Components.AppCheckBox {
            id: identityCheck
            objectName: "fusionIdentityConfirmation"
            Layout.fillWidth: true
            visible: dialog.controller.fusionIdentityWarning !== ""
            text: "已核对两个来源，确认进行人工配对"
        }
        RowLayout {
            Layout.fillWidth: true
            Text { text: "CT 固定 · PET 叠加"; color: Theme.textMuted; font.pixelSize: 11 }
            Item { Layout.fillWidth: true }
            Components.AppButton { text: "取消"; onClicked: dialog.controller.cancelFusion() }
            Components.AppButton {
                objectName: "confirmFusion"
                text: "融合浏览"
                normalColor: Theme.selectionBackground
                textColor: Theme.primaryColor
                enabled: dialog.controller.fusionCanConfirm
                    && (dialog.controller.fusionIdentityWarning === "" || identityCheck.checked)
                onClicked: dialog.controller.confirmFusion(identityCheck.checked)
            }
        }
    }
}
