pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"

Item {
    id: emptyState
    objectName: "workspaceEmptyState"

    required property var panelController
    property var pacsController: null
    property var workspaceController: null

    readonly property bool scanning:
        emptyState.panelController?.scanning ?? false
    readonly property int seriesCount:
        emptyState.panelController?.seriesItems?.length ?? 0
    readonly property bool hasSeries: seriesCount > 0

    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(440, Math.max(220, emptyState.width - 72))
        spacing: 12

        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 64
            Layout.preferredHeight: 64

            radius: 18
            color: Theme.primarySoft
            border.color: Theme.selectionBorder
            border.width: 1

            Components.AppIcon {
                objectName: "homeFolderIcon"
                anchors.centerIn: parent
                visible: !emptyState.hasSeries
                iconName: "nav-load-file"
                iconSize: 30
                iconColor: Theme.primaryColor
                opacity: emptyState.scanning ? 0.55 : 1
            }

            Text {
                anchors.centerIn: parent
                visible: emptyState.hasSeries
                text: emptyState.seriesCount
                color: Theme.primaryHover
                font.pixelSize: 21
                font.weight: Font.DemiBold
            }
        }

        Text {
            Layout.fillWidth: true
            Layout.topMargin: 4

            text: {
                if (emptyState.scanning && !emptyState.hasSeries)
                    return "正在扫描 DICOM 文件"
                if (emptyState.hasSeries)
                    return "选择一个影像序列"
                return "加载 DICOM 影像"
            }
            color: Theme.textPrimary
            font.pixelSize: 22
            font.weight: Font.DemiBold
            horizontalAlignment: Text.AlignHCenter
        }

        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 92
            Layout.preferredHeight: 1
            color: Theme.selectionBorder
            opacity: 0.8
        }

        Text {
            Layout.fillWidth: true

            text: {
                if (emptyState.scanning && !emptyState.hasSeries)
                    return "正在读取文件并整理可用序列，请稍候。"
                if (emptyState.hasSeries)
                    return "已发现 " + emptyState.seriesCount
                        + " 个序列。请在左侧选择序列，然后双击打开影像。"
                return emptyState.pacsController && emptyState.pacsController.pacsEnabled
                    ? (emptyState.pacsController.localEnabled
                        ? "从本地文件夹或 PACS 导入 DICOM 影像，开始浏览序列。"
                        : "从 PACS 查询并导入 DICOM 影像，开始浏览序列。")
                    : "打开一个包含 DICOM 文件的文件夹，程序会自动扫描并整理可用序列。"
            }
            color: Theme.textMuted
            font.pixelSize: 13
            lineHeight: 1.45
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
        }

        Components.AppButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 8
            Layout.preferredWidth: 168

            visible: !emptyState.hasSeries && (!emptyState.pacsController || emptyState.pacsController.localEnabled)
            enabled: !emptyState.scanning
            text: emptyState.scanning ? "正在扫描…" : "打开 DICOM 文件夹"
            objectName: "homeOpenFolder"
            iconName: "nav-load-file"
            iconSize: 17
            normalColor: Theme.primaryButtonBackground
            hoverColor: Theme.primaryButtonHover
            pressedColor: Theme.primaryButtonPressed
            disabledColor: Theme.primaryButtonDisabled
            focusBorderColor: Theme.primaryButtonBorder
            textColor: Theme.textOnPrimary

            onClicked: emptyState.panelController.openFolderDialog()
        }
        Components.AppButton {
            objectName: "homeOpenPacs"
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 168
            visible: emptyState.pacsController && emptyState.pacsController.pacsEnabled
            text: "从 PACS 导入序列"
            iconName: "nav-pacs"
            iconSize: 17
            normalColor: Theme.primaryButtonBackground
            hoverColor: Theme.primaryButtonHover
            pressedColor: Theme.primaryButtonPressed
            disabledColor: Theme.primaryButtonDisabled
            focusBorderColor: Theme.primaryButtonBorder
            textColor: Theme.textOnPrimary
            onClicked: emptyState.workspaceController.openPacs()
        }

    }
}
