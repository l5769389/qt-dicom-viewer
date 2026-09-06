pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../../../components" as Components
import "../../../theme"

ColumnLayout {
    id: petPanel
    objectName: "petIntensityPanel"

    required property var viewportController
    spacing: 12

    function formatValue(value) {
        if (!Number.isFinite(value))
            return "--"
        const precision = Math.abs(value) >= 1000 ? 0
            : Math.abs(value) >= 10 ? 2 : 3
        const result = Number(value).toFixed(precision)
        return precision === 0 ? result : result.replace(/\.?0+$/, "")
    }

    Text {
        text: "PET 强度范围"
        color: Theme.textPrimary
        font.pixelSize: 14
        font.weight: Font.DemiBold
    }
    Text {
        visible: petPanel.viewportController ? petPanel.viewportController.petUnitPending : false
        text: "正在切换单位…"
        color: Theme.textMuted
        font.pixelSize: 12
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: rangeContent.implicitHeight + 24
        color: Theme.cardBackground
        border.color: Theme.borderSubtle
        radius: 8

        ColumnLayout {
            id: rangeContent
            anchors.fill: parent
            anchors.margins: 12
            spacing: 10

            RowLayout {
                Layout.fillWidth: true

                Text {
                    Layout.fillWidth: true
                    text: "当前显示上限"
                    color: Theme.textMuted
                    font.pixelSize: 12
                }

                Components.AppTextField {
                    id: displayUpperInput
                    objectName: "petDisplayUpperInput"
                    Layout.preferredWidth: 92
                    implicitHeight: 32
                    horizontalAlignment: Text.AlignRight
                    color: Theme.textPrimary
                    selectionColor: Theme.selectionBackground
                    validator: DoubleValidator {
                        bottom: petPanel.viewportController
                            ? petPanel.viewportController.petMinimumUpper
                            : 0.001
                    }
                    text: petPanel.formatValue(
                        petPanel.viewportController
                            ? petPanel.viewportController.petDisplayUpper
                            : 0
                    )
                    onEditingFinished: {
                        const parsed = Number(text)
                        if (Number.isFinite(parsed))
                            petPanel.viewportController.setPetDisplayUpper(parsed)
                        text = Qt.binding(() => petPanel.formatValue(petPanel.viewportController.petDisplayUpper))
                    }
                }
            }

            Basic.Slider {
                id: displayUpperSlider
                objectName: "petDisplayUpperSlider"
                Layout.fillWidth: true
                from: petPanel.viewportController
                    ? petPanel.viewportController.petMinimumUpper
                    : 0.001
                to: Math.max(
                    from,
                    petPanel.viewportController
                        ? petPanel.viewportController.petControlUpper
                        : 1
                )
                value: petPanel.viewportController
                    ? petPanel.viewportController.petDisplayUpper
                    : 0
                onMoved: petPanel.viewportController.setPetDisplayUpper(value)

                background: Rectangle {
                    x: displayUpperSlider.leftPadding
                    y: displayUpperSlider.topPadding
                        + displayUpperSlider.availableHeight / 2 - height / 2
                    width: displayUpperSlider.availableWidth
                    height: 14
                    radius: 5
                    border.color: Theme.borderStrong
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0; color: "#02070e" }
                        GradientStop { position: 1; color: "#f5f7fb" }
                    }
                }

                handle: Rectangle {
                    x: displayUpperSlider.leftPadding
                        + displayUpperSlider.visualPosition
                        * (displayUpperSlider.availableWidth - width)
                    y: displayUpperSlider.topPadding
                        + displayUpperSlider.availableHeight / 2 - height / 2
                    width: 16
                    height: 26
                    radius: 6
                    color: Theme.primaryColor
                    border.color: Theme.textOnPrimary
                }
            }

            RowLayout {
                Layout.fillWidth: true

                Text {
                    Layout.fillWidth: true
                    text: "控制上限"
                    color: Theme.textMuted
                    font.pixelSize: 12
                }

                Components.AppTextField {
                    objectName: "petControlUpperInput"
                    Layout.preferredWidth: 92
                    implicitHeight: 32
                    horizontalAlignment: Text.AlignRight
                    text: petPanel.formatValue(
                        petPanel.viewportController
                            ? petPanel.viewportController.petControlUpper
                            : 0
                    )
                    color: Theme.textPrimary
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                    validator: DoubleValidator { bottom: 0.001 }
                    onEditingFinished: {
                        const value = Number(text)
                        if (Number.isFinite(value))
                            petPanel.viewportController.setPetControlUpper(value)
                        text = Qt.binding(() => petPanel.formatValue(petPanel.viewportController.petControlUpper))
                    }
                }
            }

            GridLayout {
                Layout.fillWidth: true
                columns: petPanel.width < 240 ? 4 : 5
                columnSpacing: 6
                rowSpacing: 6

                Repeater {
                    model: petPanel.viewportController
                        ? petPanel.viewportController.petControlUpperOptions
                        : []

                    delegate: Components.AppButton {
                        required property var modelData
                        Layout.fillWidth: true
                        compact: true
                        checkable: true
                        checked: Math.abs(
                            Number(modelData)
                            - petPanel.viewportController.petControlUpper
                        ) < 0.000001
                        text: petPanel.formatValue(Number(modelData))
                        onClicked: petPanel.viewportController.setPetControlUpper(
                            Number(modelData)
                        )
                    }
                }
            }
        }
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: unitContent.implicitHeight + 24
        color: Theme.cardBackground
        border.color: Theme.borderSubtle
        radius: 8

        ColumnLayout {
            id: unitContent
            anchors.fill: parent
            anchors.margins: 12
            spacing: 10

            RowLayout {
                Layout.fillWidth: true

                Text {
                    Layout.fillWidth: true
                    text: "单位"
                    color: Theme.textMuted
                    font.pixelSize: 12
                }

                Text {
                    text: petPanel.viewportController
                        ? petPanel.viewportController.petActiveUnitLabel
                        : ""
                    color: Theme.textPrimary
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }
            }

            GridLayout {
                Layout.fillWidth: true
                columns: petPanel.width < 260 ? 1 : 2
                columnSpacing: 8
                rowSpacing: 8

                Repeater {
                    model: petPanel.viewportController
                        ? petPanel.viewportController.petUnitOptions
                        : []

                    delegate: Components.AppButton {
                        required property var modelData
                        objectName: "petUnit-" + modelData.unitId
                        Layout.fillWidth: true
                        checkable: true
                        checked: modelData.active
                        enabled: modelData.enabled
                        text: modelData.label
                        fontPixelSize: 11
                        onClicked: petPanel.viewportController.setPetUnit(
                            modelData.unitId
                        )
                        Basic.ToolTip.visible: hovered
                            && modelData.warning !== ""
                        Basic.ToolTip.delay: 350
                        Basic.ToolTip.text: modelData.warning
                    }
                }
            }
        }
    }

}
