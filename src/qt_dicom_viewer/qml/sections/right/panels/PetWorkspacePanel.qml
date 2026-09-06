pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../../../components" as Components
import "../../../theme"

ColumnLayout {
    id: panel
    objectName: "petWorkspacePanel"
    required property var controller
    spacing: 12

    Text {
        Layout.fillWidth: true
        text: panel.controller.isFusion ? "PET/CT 融合浏览" : "PET MPR · 三平面 + MIP"
        color: Theme.textPrimary
        font.pixelSize: 14
        font.bold: true
    }
    Text {
        Layout.fillWidth: true
        visible: text !== ""
        text: panel.controller.warning
        color: Theme.warningColor
        font.pixelSize: 12
        wrapMode: Text.Wrap
    }
    RowLayout {
        visible: panel.controller.isFusion
        Layout.fillWidth: true
        Repeater {
            model: [{name:"轴位", value:"axial"}, {name:"冠状位", value:"coronal"}, {name:"矢状位", value:"sagittal"}]
            delegate: Components.AppButton {
                required property var modelData
                Layout.fillWidth: true
                objectName: "fusionPlane-" + modelData.value
                text: modelData.name
                checkable: true
                checked: panel.controller.plane === modelData.value
                onClicked: panel.controller.setPlane(modelData.value)
            }
        }
    }
    ColumnLayout {
        visible: panel.controller.isFusion
        Layout.fillWidth: true
        Text { text: "CT 调窗"; color: Theme.textPrimary; font.bold: true }
        RowLayout {
            Layout.fillWidth: true
            Text { text: "WL"; color: Theme.textMuted }
            Basic.TextField {
                objectName: "fusionCtCenter"
                Layout.fillWidth: true
                text: Number(panel.controller.ctCenter).toFixed(1)
                color: Theme.textPrimary
                background: Rectangle { color: Theme.panelBackgroundStrong; border.color: Theme.borderDefault; radius: 5 }
                validator: DoubleValidator {}
                onEditingFinished: {
                    panel.controller.setCtWindow(Number(text), panel.controller.ctWidth)
                    text = Qt.binding(() => Number(panel.controller.ctCenter).toFixed(1))
                }
            }
            Text { text: "WW"; color: Theme.textMuted }
            Basic.TextField {
                objectName: "fusionCtWidth"
                Layout.fillWidth: true
                text: Number(panel.controller.ctWidth).toFixed(1)
                color: Theme.textPrimary
                background: Rectangle { color: Theme.panelBackgroundStrong; border.color: Theme.borderDefault; radius: 5 }
                validator: DoubleValidator { bottom: 1 }
                onEditingFinished: {
                    panel.controller.setCtWindow(panel.controller.ctCenter, Number(text))
                    text = Qt.binding(() => Number(panel.controller.ctWidth).toFixed(1))
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Repeater {
                model: [{name:"肺", c:-600, w:1500}, {name:"骨", c:400, w:1800}, {name:"软组织", c:40, w:400}]
                delegate: Components.AppButton {
                    required property var modelData
                    Layout.fillWidth: true
                    text: modelData.name
                    compact: true
                    onClicked: panel.controller.setCtWindow(modelData.c, modelData.w)
                }
            }
        }
    }
    PetIntensityPanel {
        Layout.fillWidth: true
        viewportController: panel.controller.petController
    }
    RowLayout {
        Layout.fillWidth: true
        Text { text: "PET 色表"; color: Theme.textMuted }
        Components.AppComboBox {
            objectName: "petColorMap"
            Layout.fillWidth: true
            model: panel.controller.petController.colorMapOptions
            textRole: "label"
            currentIndex: model.findIndex(entry => entry.colorMap === panel.controller.petColorMap)
            onActivated: panel.controller.setPetColorMap(model[currentIndex].colorMap)
        }
    }
    ColumnLayout {
        visible: panel.controller.isFusion
        Layout.fillWidth: true
        RowLayout {
            Text { text: "融合 PET 色表"; color: Theme.textMuted }
            Components.AppComboBox {
                objectName: "fusionColorMap"
                Layout.fillWidth: true
                model: panel.controller.petController.colorMapOptions
                textRole: "label"
                currentIndex: model.findIndex(entry => entry.colorMap === panel.controller.fusionColorMap)
                onActivated: panel.controller.setFusionColorMap(model[currentIndex].colorMap)
            }
        }
        Text { text: "PET 叠加比例 " + Math.round(panel.controller.opacity * 100) + "%"; color: Theme.textPrimary }
        Basic.Slider {
            objectName: "fusionOpacity"
            Layout.fillWidth: true
            from: 0; to: 1
            value: panel.controller.opacity
            onMoved: panel.controller.setOpacity(value)
        }
        Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: Theme.borderDefault }
        Text {
            Layout.fillWidth: true
            text: "配准 · " + panel.controller.registrationStatus
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
            text: "PET / 融合格：左拖平移，右拖旋转，Esc 退出"
            color: Theme.textMuted
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            enabled: panel.controller.ready
            Repeater {
                model: ["X 平移 (mm)", "Y 平移 (mm)", "Z 平移 (mm)", "X 旋转 (°)", "Y 旋转 (°)", "Z 旋转 (°)"]
                delegate: ColumnLayout {
                    required property string modelData
                    required property int index
                    Layout.fillWidth: true
                    Text { text: parent.modelData; color: Theme.textMuted; font.pixelSize: 11 }
                    Basic.TextField {
                        objectName: "registrationParameter-" + parent.index
                        Layout.fillWidth: true
                        color: Theme.textPrimary
                        background: Rectangle { color: Theme.panelBackgroundStrong; border.color: Theme.borderDefault; radius: 5 }
                        text: Number(panel.controller.registrationParameters[parent.index]).toFixed(2)
                        validator: DoubleValidator {}
                        onEditingFinished: {
                            panel.controller.setRegistrationParameter(parent.index, Number(text))
                            text = Qt.binding(() => Number(panel.controller.registrationParameters[parent.index]).toFixed(2))
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
}
