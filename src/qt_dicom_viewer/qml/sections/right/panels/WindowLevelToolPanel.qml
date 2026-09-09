pragma
ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../../../theme"
import "../../../components" as Components

ColumnLayout {
    id: windowPanel

    required property var presets
    property real currentCenter: NaN
    property real currentWidth: NaN
    property var settingsController: null
    property bool allowEditing: true
    property bool supportsInversion: false
    property bool inverted: false
    signal inversionRequested()
    property string centerObjectName: "windowCenterInput"
    property string widthObjectName: "windowWidthInput"
    property bool dirty: false
    property bool namingTemplate: false
    property string errorText: ""
    readonly property bool ready: Number.isFinite(currentCenter) && Number.isFinite(currentWidth)
    spacing: 8

    function syncInputs() {
        if (dirty) return
        widthInput.text = Number.isFinite(currentWidth) ? String(currentWidth) : ""
        centerInput.text = Number.isFinite(currentCenter) ? String(currentCenter) : ""
    }
    function values() {
        const width = widthInput.text.trim() ? Number(widthInput.text) : NaN
        const center = centerInput.text.trim() ? Number(centerInput.text) : NaN
        if (!Number.isFinite(width) || width < 1 || width > 1000000
                || !Number.isFinite(center) || center < -1000000 || center > 1000000) {
            errorText = "窗宽应为 1–1000000，窗位应为 -1000000–1000000"
            return null
        }
        errorText = ""
        return {width: width, center: center}
    }
    function applyInput() {
        const value = values()
        if (!value || !ready) return
        actionTriggered("", value.center, value.width)
        dirty = false
        syncInputs()
    }
    function saveTemplate() {
        const value = values()
        if (!value || !settingsController) return
        if (settingsController.saveWindowTemplate("", templateName.text, value.width, value.center)) {
            namingTemplate = false
            templateName.text = ""
        } else {
            errorText = settingsController.message
        }
    }
    onCurrentCenterChanged: syncInputs()
    onCurrentWidthChanged: syncInputs()
    Component.onCompleted: syncInputs()

    signal actionTriggered(
        string presetId,
        real center,
        real width
    )


    ColumnLayout {
        visible: windowPanel.allowEditing
        Layout.fillWidth: true
        spacing: 8
        RowLayout {
            Layout.fillWidth: true
            uniformCellSizes: true
            spacing: 8
            ColumnLayout {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                Text { text: "窗宽 · WW"; color: Theme.textMuted; font.pixelSize: 12 }
                Components.AppTextField {
                    id: widthInput
                    objectName: windowPanel.widthObjectName
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    implicitWidth: 0
                    Layout.minimumHeight: Theme.controlHeight
                    Layout.maximumHeight: Theme.controlHeight
                    Layout.preferredHeight: Theme.controlHeight
                    enabled: windowPanel.ready
                    Accessible.name: "窗宽 WW"
                    selectByMouse: true
                    onTextEdited: windowPanel.dirty = true
                    onAccepted: windowPanel.applyInput()
                    Keys.onEscapePressed: { windowPanel.dirty = false; windowPanel.syncInputs() }
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                Text { text: "窗位 · WL"; color: Theme.textMuted; font.pixelSize: 12 }
                Components.AppTextField {
                    id: centerInput
                    objectName: windowPanel.centerObjectName
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    implicitWidth: 0
                    Layout.minimumHeight: Theme.controlHeight
                    Layout.maximumHeight: Theme.controlHeight
                    Layout.preferredHeight: Theme.controlHeight
                    enabled: windowPanel.ready
                    Accessible.name: "窗位 WL"
                    selectByMouse: true
                    onTextEdited: windowPanel.dirty = true
                    onAccepted: windowPanel.applyInput()
                    Keys.onEscapePressed: { windowPanel.dirty = false; windowPanel.syncInputs() }
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Components.AppButton {
                objectName: "applyWindowValues"
                normalColor: Theme.primaryButtonBackground
                hoverColor: Theme.primaryButtonHover
                pressedColor: Theme.primaryButtonPressed
                disabledColor: Theme.primaryButtonDisabled
                textColor: Theme.textOnPrimary
                fontWeight: Font.DemiBold
                text: "应用"
                compact: true
                Layout.fillWidth: true
                enabled: windowPanel.ready
                onClicked: windowPanel.applyInput()
            }
            Components.AppButton {
                objectName: "beginSaveWindowTemplate"
                normalColor: "transparent"
                baseBorderWidth: 1
                baseBorderColor: Theme.controlBorder
                textColor: Theme.textSecondary
                text: "保存为模板"
                compact: true
                Layout.fillWidth: true
                enabled: windowPanel.ready && !!windowPanel.settingsController
                onClicked: {
                    if (!windowPanel.values()) return
                    windowPanel.namingTemplate = true
                    templateName.forceActiveFocus()
                }
            }
        }
        ColumnLayout {
            visible: windowPanel.namingTemplate
            Layout.fillWidth: true
            Components.AppTextField {
                id: templateName
                objectName: "quickWindowTemplateName"
                Layout.fillWidth: true
                placeholderText: "模板名称"
                maximumLength: 40
                onAccepted: windowPanel.saveTemplate()
            }
            RowLayout {
                Layout.fillWidth: true
                Components.AppButton {
                    objectName: "quickSaveWindowTemplate"
                    normalColor: Theme.primaryButtonBackground
                    hoverColor: Theme.primaryButtonHover
                    pressedColor: Theme.primaryButtonPressed
                    disabledColor: Theme.primaryButtonDisabled
                    textColor: Theme.textOnPrimary
                    fontWeight: Font.DemiBold
                    text: "保存"; compact: true; Layout.fillWidth: true
                    onClicked: windowPanel.saveTemplate()
                }
                Components.AppButton {
                    objectName: "cancelSaveWindowTemplate"
                    text: "取消"; compact: true; Layout.fillWidth: true
                    normalColor: "transparent"
                    textColor: Theme.textMuted
                    onClicked: { windowPanel.namingTemplate = false; windowPanel.errorText = "" }
                }
            }
        }
        Text {
            objectName: "windowInputError"
            Layout.fillWidth: true
            visible: text !== ""
            text: windowPanel.errorText
            color: Theme.dangerColor
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }
    }

    Components.AppButton {
        objectName: "invertWindowButton"
        Layout.fillWidth: true
        visible: windowPanel.supportsInversion
        enabled: windowPanel.ready
        compact: true
        iconName: "invert"
        text: "反白"
        checked: windowPanel.inverted
        normalColor: "transparent"
        baseBorderWidth: 1
        baseBorderColor: Theme.controlBorder
        Accessible.name: "反白"
        Accessible.description: "切换 CT 显示明暗，保留窗宽和窗位"
        onClicked: windowPanel.inversionRequested()
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 28
        Layout.maximumHeight: 28
        color: Theme.secondarySoft
        radius: 4

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            spacing: 8

            Text {
                font.pixelSize: Theme.bodyFontSize
                Layout.fillWidth: true
                text: "预设"
                color: Theme.textMuted
            }

            Text {
                font.pixelSize: Theme.bodyFontSize
                Layout.preferredWidth: 44
                text: "WL"
                color: Theme.textMuted
                horizontalAlignment: Text.AlignRight
            }

            Text {
                font.pixelSize: Theme.bodyFontSize
                Layout.preferredWidth: 44
                text: "WW"
                color: Theme.textMuted
                horizontalAlignment: Text.AlignRight
            }
            Item { Layout.preferredWidth: 22; visible: windowPanel.allowEditing }
        }
    }

    ListView {
        id: presetList

        Layout.fillWidth: true
        Layout.preferredHeight: contentHeight
        Layout.maximumHeight: contentHeight
        implicitHeight: contentHeight
        spacing: 4
        clip: true
        interactive: false
        model: windowPanel.presets

        delegate: Basic.ItemDelegate
        {
            id: presetItem

            required property var modelData
            objectName: "windowPreset-" + modelData.presetId

            width: presetList.width
            height: 36
            leftPadding: 10
            rightPadding: 10
            topPadding: 0
            bottomPadding: 0
            hoverEnabled: true
            checked: Number.isFinite(windowPanel.currentCenter) && Number.isFinite(windowPanel.currentWidth)
                && Math.abs(windowPanel.currentCenter - Number(modelData.center)) < 0.01
                && Math.abs(windowPanel.currentWidth - Number(modelData.width)) < 0.01

            onClicked: {
                windowPanel.dirty = false
                windowPanel.errorText = ""
                windowPanel.actionTriggered(
                    modelData.presetId,
                    Number(modelData.center),
                    Number(modelData.width)
                )
                windowPanel.syncInputs()
            }

            contentItem: Item {
                RowLayout {
                    anchors.fill: parent
                    spacing: 8

                    Text {
                        Layout.fillHeight: true
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: Theme.bodyFontSize
                        Layout.fillWidth: true
                        text: presetItem.modelData.label
                        color: Theme.textPrimary
                        elide: Text.ElideRight
                    }

                    Text {
                        Layout.fillHeight: true
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: Theme.bodyFontSize
                        Layout.preferredWidth: 44
                        text: presetItem.modelData.center
                        color: Theme.textSecondary
                        horizontalAlignment: Text.AlignRight
                    }

                    Text {
                        Layout.fillHeight: true
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: Theme.bodyFontSize
                        Layout.preferredWidth: 44
                        text: presetItem.modelData.width
                        color: Theme.textSecondary
                        horizontalAlignment: Text.AlignRight
                    }
                    Item {
                        Layout.preferredWidth: 22
                        Layout.preferredHeight: 24
                        Layout.alignment: Qt.AlignVCenter
                        visible: windowPanel.allowEditing
                        Components.ToolbarAction {
                            anchors.fill: parent
                            visible: presetItem.modelData.builtin === false
                            actionEnabled: !!windowPanel.settingsController
                            buttonObjectName: "quickDeleteWindowTemplate-" + presetItem.modelData.presetId
                            label: "删除模板"
                            iconName: "delete"
                            iconSize: 16
                            resetAction: true
                            onTriggered: {
                                windowPanel.errorText = windowPanel.settingsController.deleteWindowTemplate(presetItem.modelData.presetId)
                                    ? "" : windowPanel.settingsController.message
                            }
                        }
                    }
                }
            }

            background: Rectangle {
                color: presetItem.pressed
                    ? Theme.controlPressed
                    : presetItem.checked
                        ? Theme.selectionBackground
                    : presetItem.hovered
                        ? Theme.controlHover
                        : "transparent"
                radius: 5
                border.width: presetItem.visualFocus ? 2 : presetItem.checked ? 1 : 0
                border.color: presetItem.visualFocus ? Theme.focusBorder : Theme.selectionBorder
            }
        }
    }
    Item {
        Layout.fillHeight: true
    }
}
