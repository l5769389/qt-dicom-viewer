pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"

Components.AppDialog {
    id: dialog
    objectName: "pacsProfileDialog"
    title: profileId ? "编辑 PACS 配置" : "新增 PACS 配置"
    closeEnabled: !pacsController.busy
    required property var pacsController
    property string profileId: ""
    property string saveError: ""
    property bool profileEnabled: true
    property bool existingSecret: false
    parent: Basic.Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(540, parent.width - 40)
    height: Math.min(665, parent.height - 36)
    padding: 16
    modal: true
    focus: true

    function edit(profile) {
        saveError = "";
        profileId = profile ? profile.id : "";
        profileEnabled = profile ? profile.enabled : true;
        existingSecret = profile ? !profile.needsSecret && profile.auth !== "none" : false;
        nameField.text = profile ? profile.name : "";
        urlField.text = profile ? profile.url : "";
        authField.currentIndex = profile ? ["none", "basic", "bearer"].indexOf(profile.auth) : 0;
        usernameField.text = profile ? profile.username : "";
        secretField.text = "";
        timeoutField.text = profile ? String(profile.timeout) : "15";
        pacsController.clearDraftTest();
        open();
    }
    function values() {
        return {
            id: profileId,
            name: nameField.text,
            url: urlField.text,
            enabled: profileEnabled,
            auth: ["none", "basic", "bearer"][authField.currentIndex],
            username: usernameField.text,
            secret: secretField.text,
            timeout: timeoutField.text
        };
    }
    onClosed: secretField.text = ""

    contentItem: ColumnLayout {
        spacing: 12

        Basic.ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            id: profileScroll
            contentWidth: availableWidth
            Basic.ScrollBar.horizontal.policy: Basic.ScrollBar.AlwaysOff
            rightPadding: 12
            Basic.ScrollBar.vertical: Components.AppScrollBar {}
            clip: true
            ColumnLayout {
                width: profileScroll.availableWidth
                spacing: 8
                Text {
                    text: "配置名称"
                    color: Theme.textMuted
                    font.pixelSize: 12
                }
                Components.AppTextField {
                    id: nameField
                    objectName: "pacsProfileName"
                    Layout.fillWidth: true
                    placeholderText: "例如：Orthanc Local"
                    enabled: !dialog.pacsController.busy
                    onTextEdited: dialog.pacsController.clearDraftTest()
                }
                Text {
                    text: "DICOMweb 根地址"
                    color: Theme.textMuted
                    font.pixelSize: 12
                    Layout.topMargin: 4
                }
                Components.AppTextField {
                    id: urlField
                    objectName: "pacsProfileUrl"
                    Layout.fillWidth: true
                    placeholderText: "http://127.0.0.1:8042/dicom-web"
                    enabled: !dialog.pacsController.busy
                    onTextEdited: dialog.pacsController.clearDraftTest()
                }
                Text {
                    Layout.fillWidth: true
                    text: "填写 PACS 的 DICOMweb 服务地址，包含路径。"
                    color: Theme.textSubtle
                    wrapMode: Text.Wrap
                    font.pixelSize: 11
                }
                Text {
                    text: "认证方式"
                    color: Theme.textMuted
                    font.pixelSize: 12
                    Layout.topMargin: 4
                }
                Components.AppComboBox {
                    id: authField
                    objectName: "pacsProfileAuth"
                    Layout.fillWidth: true
                    model: ["无认证", "Basic · 用户名与密码", "Bearer · 访问令牌"]
                    enabled: !dialog.pacsController.busy
                    onActivated: dialog.pacsController.clearDraftTest()
                }
                Text {
                    visible: authField.currentIndex === 1
                    text: "用户名"
                    color: Theme.textMuted
                    font.pixelSize: 12
                }
                Components.AppTextField {
                    id: usernameField
                    objectName: "pacsProfileUsername"
                    visible: authField.currentIndex === 1
                    Layout.fillWidth: true
                    enabled: !dialog.pacsController.busy
                    onTextEdited: dialog.pacsController.clearDraftTest()
                }
                Text {
                    visible: authField.currentIndex > 0
                    text: authField.currentIndex === 1 ? "密码" : "访问令牌"
                    color: Theme.textMuted
                    font.pixelSize: 12
                }
                Components.AppTextField {
                    id: secretField
                    objectName: "pacsProfileSecret"
                    visible: authField.currentIndex > 0
                    Layout.fillWidth: true
                    echoMode: TextInput.Password
                    placeholderText: dialog.existingSecret ? "留空保留本次会话的认证信息" : "仅保留在本次会话"
                    enabled: !dialog.pacsController.busy
                    onTextEdited: dialog.pacsController.clearDraftTest()
                }
                Text {
                    visible: authField.currentIndex > 0
                    Layout.fillWidth: true
                    text: "密码和令牌不保存到磁盘；重启后需重新填写。"
                    color: Theme.textSubtle
                    font.pixelSize: 11
                    wrapMode: Text.Wrap
                }
                Text {
                    text: "网络超时（秒）"
                    color: Theme.textMuted
                    font.pixelSize: 12
                    Layout.topMargin: 4
                }
                Components.AppTextField {
                    id: timeoutField
                    objectName: "pacsProfileTimeout"
                    Layout.fillWidth: true
                    validator: IntValidator {
                        bottom: 3
                        top: 120
                    }
                    enabled: !dialog.pacsController.busy
                    onTextEdited: dialog.pacsController.clearDraftTest()
                }

            }
        }
        Text {
            objectName: "pacsProfileMessage"
            Layout.fillWidth: true
            visible: text !== ""
            text: dialog.saveError || dialog.pacsController.draftTestResult.message || ""
            color: dialog.saveError || dialog.pacsController.draftTestResult.state === "error" ? Theme.dangerColor
                : dialog.pacsController.draftTestResult.state === "success" ? Theme.successColor : Theme.textSecondary
            wrapMode: Text.Wrap; font.pixelSize: 12
        }

    }
    footer: Components.AppDialogFooter {
        leading: Components.AppButton {
            objectName: "pacsTestDraft"
            text: dialog.pacsController.busy ? "测试中…" : "测试连接"
            enabled: !dialog.pacsController.busy
            onClicked: { dialog.saveError = ""; dialog.pacsController.testDraft(dialog.values()) }
        }
        Components.AppButton {
            objectName: "pacsCancelProfile"
            text: "取消"
            enabled: !dialog.pacsController.busy
            onClicked: dialog.reject()
        }
        Components.AppButton {
            objectName: "pacsSaveProfile"
            text: "保存配置"
            actionRole: "primary"
            enabled: !dialog.pacsController.busy
            onClicked: {
                if (dialog.pacsController.saveProfile(dialog.values())) dialog.accept()
                else dialog.saveError = dialog.pacsController.message
            }
        }
    }
}
