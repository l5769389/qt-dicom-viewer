pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../../components" as Components
import "../../../theme"

ColumnLayout {
    id: panel
    objectName: "petRegistrationPanel"
    required property var controller
    spacing: 12
    Text { text: "PET/CT 配准"; color: Theme.textPrimary; font.pixelSize: 14; font.bold: true }
    Text {
        Layout.fillWidth: true
        text: "固定 CT，调整 PET 的位置。请在三个切面核对对齐效果。"
        color: Theme.textMuted
        wrapMode: Text.Wrap
        font.pixelSize: 12
    }
        Text {
            Layout.fillWidth: true
            visible: panel.controller.registrationStatus !== ""
            text: panel.controller.registrationStatus
            color: Theme.textPrimary
            wrapMode: Text.Wrap
        }
        Components.AppButton {
            objectName: "togglePetRegistration"
            Layout.fillWidth: true
            enabled: panel.controller.ready
            text: panel.controller.registrationActive ? "退出手动配准" : "开始手动配准"
            onClicked: panel.controller.setRegistrationActive(!panel.controller.registrationActive)
        }
        Text {
            Layout.fillWidth: true
            visible: panel.controller.registrationActive
            text: "PET / 融合格：左拖平移，右拖旋转，视图随拖动更新。松开后细化 MIP。Esc 或切换工具结束调整并保留结果。"
            color: Theme.textMuted
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            enabled: panel.controller.ready && panel.controller.registrationActive
            Repeater {
                model: [
                    {label: "X 平移 (mm)", parameter: 0}, {label: "X 旋转 (°)", parameter: 3},
                    {label: "Y 平移 (mm)", parameter: 1}, {label: "Y 旋转 (°)", parameter: 4},
                    {label: "Z 平移 (mm)", parameter: 2}, {label: "Z 旋转 (°)", parameter: 5}
                ]
                delegate: ColumnLayout {
                    id: parameterRow
                    required property var modelData
                    Layout.fillWidth: true
                    Text { text: parameterRow.modelData.label; color: Theme.textMuted; font.pixelSize: 11 }
                    Components.AppNumberField {
                        objectName: "registrationParameter-" + parameterRow.modelData.parameter
                        Layout.fillWidth: true
                        color: Theme.textPrimary
                        numberValue: panel.controller.registrationParameters[parameterRow.modelData.parameter]
                        minimum: -10000
                        maximum: 10000
                        decimals: 2
                        onEdited: value => panel.controller.setRegistrationParameter(parameterRow.modelData.parameter, value)
                        Keys.onEscapePressed: {
                            sync()
                            panel.controller.setRegistrationActive(false)
                        }
                        onEditingFinished: {
                            sync()
                            panel.controller.finishRegistrationPreview()
                        }
                    }
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Components.AppButton { Layout.fillWidth: true; text: "中心对齐"; enabled: panel.controller.ready; onClicked: panel.controller.centerAlign() }
            Components.AppButton { Layout.fillWidth: true; text: "重置配准"; enabled: panel.controller.ready; onClicked: panel.controller.resetRegistration() }
        }
        RowLayout {
            Layout.fillWidth: true
            Components.AppButton { Layout.fillWidth: true; text: "加载配准"; enabled: panel.controller.ready; onClicked: panel.controller.loadRegistration() }
            Components.AppButton { Layout.fillWidth: true; text: "保存配准"; enabled: panel.controller.ready; onClicked: panel.controller.saveRegistration() }
        }

}
