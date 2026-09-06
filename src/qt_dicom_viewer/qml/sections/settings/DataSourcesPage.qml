pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"

Basic.ScrollView {
    id: page
    required property var pacsController
    objectName: "settingsScroll"
    contentWidth: availableWidth
    rightPadding: 12
    clip: true
    Basic.ScrollBar.vertical: Components.AppScrollBar {}
    ColumnLayout {
        width: Math.min(page.availableWidth, 1000)
        spacing: 12
        Text {
            Layout.fillWidth: true
            Layout.margins: 16
            Layout.bottomMargin: 0
            text: "PACS 数据源"
            color: Theme.textPrimary
            font.pixelSize: 18
            font.bold: true
        }
        Text {
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            text: "管理影像来源与 DICOMweb 连接"
            color: Theme.textMuted
            font.pixelSize: 13
            wrapMode: Text.Wrap
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            implicitHeight: sourceContent.implicitHeight + 24
            color: Theme.cardBackground
            border.color: Theme.borderSubtle
            radius: Theme.controlRadius
            ColumnLayout {
                id: sourceContent
                anchors.fill: parent
                anchors.margins: 12
                spacing: 12
                Text {
                    text: "数据源模式"
                    color: Theme.textPrimary
                    font.pixelSize: 14
                    font.bold: true
                }
                Text {
                    Layout.fillWidth: true
                    text: "本地文件和 PACS 可同时启用，入口随设置显示。"
                    color: Theme.textMuted
                    font.pixelSize: 12
                    wrapMode: Text.Wrap
                }
                Components.AppCheckBox {
                    objectName: "enableLocalSource"
                    text: "启用本地文件"
                    checked: page.pacsController.localEnabled
                    enabled: !page.pacsController.busy
                    onClicked: page.pacsController.setSources(checked, page.pacsController.pacsEnabled)
                }
                Components.AppCheckBox {
                    objectName: "enablePacsSource"
                    text: "启用 PACS 浏览器"
                    checked: page.pacsController.pacsEnabled
                    enabled: !page.pacsController.busy
                    onClicked: page.pacsController.setSources(page.pacsController.localEnabled, checked)
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            Text {
                Layout.fillWidth: true
                text: "PACS 配置"
                color: Theme.textPrimary
                font.pixelSize: 14
                font.bold: true
            }
            Components.AppButton {
                objectName: "pacsAddProfile"
                text: "+  新增配置"
                normalColor: Theme.primaryButtonBackground
                enabled: !page.pacsController.busy
                onClicked: profileDialog.edit(null)
            }
        }
        Text {
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            text: "当前默认：" + page.pacsController.defaultName
            color: Theme.textMuted
            font.pixelSize: 12
            wrapMode: Text.Wrap
        }
        Repeater {
            model: page.pacsController.profiles
            delegate: Rectangle {
                id: card
                required property var modelData
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                implicitHeight: cardContent.implicitHeight + 28
                color: Theme.cardBackground
                border.color: modelData.isDefault ? Theme.borderStrong : Theme.borderSubtle
                radius: Theme.controlRadius
                ColumnLayout {
                    id: cardContent
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 9
                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            Layout.fillWidth: true
                            text: card.modelData.name
                            color: Theme.textPrimary
                            font.pixelSize: 15
                            font.bold: true
                            elide: Text.ElideRight
                        }
                        Text {
                            visible: card.modelData.isDefault
                            text: "默认"
                            color: Theme.primaryColor
                            font.pixelSize: 11
                        }
                        Components.AppCheckBox {
                            text: "启用"
                            checked: card.modelData.enabled
                            enabled: !page.pacsController.busy
                            onClicked: page.pacsController.setProfileEnabled(card.modelData.id, checked)
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        text: card.modelData.url
                        color: Theme.textMuted
                        font.pixelSize: 12
                        wrapMode: Text.WrapAnywhere
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "DICOMweb  ·  " + (card.modelData.auth === "none" ? "无认证" : card.modelData.auth === "basic" ? "Basic" : "Bearer") + "  ·  " + (card.modelData.needsSecret ? "需补充认证信息" : card.modelData.status)
                        color: card.modelData.needsSecret ? Theme.warningColor : Theme.textSubtle
                        font.pixelSize: 11
                        wrapMode: Text.Wrap
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 7
                        Components.AppButton {
                            text: "测试连接"
                            compact: true
                            enabled: !page.pacsController.busy
                            onClicked: page.pacsController.testProfile(card.modelData.id)
                        }
                        Components.AppButton {
                            objectName: "pacsEdit-" + card.modelData.id
                            text: "详情"
                            compact: true
                            enabled: !page.pacsController.busy
                            onClicked: profileDialog.edit(card.modelData)
                        }
                        Components.AppButton {
                            text: "设为默认"
                            compact: true
                            enabled: card.modelData.enabled && !card.modelData.isDefault && !page.pacsController.busy
                            onClicked: page.pacsController.setDefault(card.modelData.id)
                        }
                        Components.AppButton {
                            text: "删除"
                            compact: true
                            textColor: Theme.dangerColor
                            enabled: !page.pacsController.busy
                            onClicked: {
                                deleteDialog.profileId = card.modelData.id;
                                deleteDialog.profileName = card.modelData.name;
                                deleteDialog.open();
                            }
                        }
                    }
                }
            }
        }
        Rectangle {
            visible: page.pacsController.profiles.length === 0
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            implicitHeight: 88
            color: Theme.cardBackground
            border.color: Theme.borderSubtle
            radius: Theme.controlRadius
            Text {
                anchors.centerIn: parent
                width: parent.width - 32
                text: "尚未添加 PACS\n新增连接配置后，即可查询并导入序列。"
                horizontalAlignment: Text.AlignHCenter
                color: Theme.textMuted
                font.pixelSize: 13
                lineHeight: 1.6
                wrapMode: Text.Wrap
            }
        }
        Text {
            objectName: "pacsSettingsMessage"
            Layout.fillWidth: true
            Layout.margins: 16
            visible: page.pacsController.message !== ""
            text: page.pacsController.message
            color: page.pacsController.isError ? Theme.dangerColor : Theme.successColor
            font.pixelSize: 12
            wrapMode: Text.Wrap
        }
    }

    PacsProfileDialog {
        id: profileDialog
        pacsController: page.pacsController
    }
    Basic.Dialog {
        id: deleteDialog
        property string profileId: ""
        property string profileName: ""
        parent: Basic.Overlay.overlay
        anchors.centerIn: parent
        width: 370
        padding: 20
        modal: true
        background: Rectangle {
            color: Theme.panelBackgroundStrong
            border.color: Theme.borderStrong
            radius: 9
        }
        contentItem: ColumnLayout {
            spacing: 12
            Text {
                Layout.fillWidth: true
                text: "删除配置“" + deleteDialog.profileName + "”？"
                color: Theme.textPrimary
                wrapMode: Text.Wrap
                font.pixelSize: 15
            }
            Text {
                Layout.fillWidth: true
                text: "已导入的影像会保留。"
                color: Theme.textMuted
                font.pixelSize: 12
            }
            RowLayout {
                Item {
                    Layout.fillWidth: true
                }
                Components.AppButton {
                    text: "取消"
                    onClicked: deleteDialog.close()
                }
                Components.AppButton {
                    text: "删除配置"
                    textColor: Theme.dangerColor
                    onClicked: {
                        page.pacsController.deleteProfile(deleteDialog.profileId);
                        deleteDialog.close();
                    }
                }
            }
        }
    }
}
