pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../theme"

Basic.Dialog {
    id: dialog
    objectName: "fusionSeriesDialog"
    required property var controller
    parent: Basic.Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(740, parent ? parent.width - 32 : 740)
    height: Math.min(580, parent ? parent.height - 32 : 580)
    modal: true
    title: "PET/CT 融合 · 选择配对序列"
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
    background: Rectangle { color: Theme.panelBackground; border.color: Theme.borderDefault; radius: 10 }
    contentItem: ColumnLayout {
        spacing: 10
        Text {
            Layout.fillWidth: true
            text: "CT 为固定层，PET 为移动层。优先列出同患者、同检查序列。"
            color: Theme.textPrimary
            wrapMode: Text.Wrap
        }
        ListView {
            id: candidates
            objectName: "fusionCandidates"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 6
            model: dialog.controller.fusionCandidates
            Basic.ScrollBar.vertical: Basic.ScrollBar {}
            delegate: Basic.ItemDelegate {
                id: candidate
                required property var modelData
                objectName: "fusionCandidate-" + modelData.seriesUid
                width: candidates.width
                height: 84
                highlighted: dialog.controller.fusionPartnerUid === modelData.seriesUid
                onClicked: { identityCheck.checked = false; dialog.controller.selectFusionPartner(modelData.seriesUid) }
                background: Rectangle {
                    color: candidate.highlighted ? Theme.selectionBackground : Theme.cardBackground
                    border.color: candidate.highlighted ? Theme.primaryColor : Theme.borderDefault
                    radius: 6
                }
                contentItem: Text {
                    text: candidate.modelData.patientName + " · " + candidate.modelData.patientId
                        + " · " + candidate.modelData.studyDate + "\n"
                        + candidate.modelData.description + " · " + candidate.modelData.count + " 张\n"
                        + (candidate.modelData.error || "可构建体数据")
                    textFormat: Text.PlainText
                    color: candidate.modelData.error ? Theme.dangerColor : Theme.textPrimary
                    elide: Text.ElideRight
                    font.pixelSize: 12
                }
            }
            Text { anchors.centerIn: parent; visible: candidates.count === 0; text: "没有可配对的另一种 modality 序列"; color: Theme.textMuted }
        }
        Text { Layout.fillWidth: true; text: dialog.controller.fusionError; visible: text !== ""; color: Theme.dangerColor; wrapMode: Text.Wrap }
        Text { Layout.fillWidth: true; text: dialog.controller.fusionIdentityWarning; visible: text !== ""; color: Theme.textPrimary; wrapMode: Text.Wrap }
        Basic.CheckBox {
            id: identityCheck
            objectName: "fusionIdentityConfirmation"
            visible: dialog.controller.fusionIdentityWarning !== ""
            text: "已核对两个来源，确认进行人工配对"
        }
        RowLayout {
            Layout.alignment: Qt.AlignRight
            Basic.Button { text: "取消"; onClicked: dialog.controller.cancelFusion() }
            Basic.Button {
                objectName: "confirmFusion"
                text: "融合浏览"
                enabled: dialog.controller.fusionPartnerUid !== ""
                    && (dialog.controller.fusionIdentityWarning === "" || identityCheck.checked)
                onClicked: dialog.controller.confirmFusion(identityCheck.checked)
            }
        }
    }
}
