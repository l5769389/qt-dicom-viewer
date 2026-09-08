pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../../theme"

ColumnLayout {
    id: pseudoColorPanel
    objectName: "pseudoColorPanel"
    required property var viewportController
    property string description: "选择用于当前视口的显示色表"
    spacing: 6

    Text {
        Layout.fillWidth: true
        text: pseudoColorPanel.description
        color: Theme.textSubtle
        font.pixelSize: 11
        wrapMode: Text.Wrap
        Layout.bottomMargin: 4
    }

    Repeater {
        model: pseudoColorPanel.viewportController
            ? pseudoColorPanel.viewportController.colorMapOptions : []

        delegate: Basic.Button {
            id: colorMapButton
            required property var modelData
            objectName: "colorMap-" + modelData.colorMap
            Layout.fillWidth: true
            implicitHeight: Math.max(38, contentItem.implicitHeight + 12)
            Layout.minimumWidth: 0
            checked: pseudoColorPanel.viewportController
                && pseudoColorPanel.viewportController.activeColorMap
                    === modelData.colorMap
            onClicked: pseudoColorPanel.viewportController?.applyColorMap(
                modelData.colorMap
            )

            contentItem: RowLayout {
                spacing: 10

                Canvas {
                    id: gradientPreview
                    Layout.preferredWidth: Math.min(80, colorMapButton.width * 0.3)
                    Layout.preferredHeight: 16

                    onPaint: {
                        const context = getContext("2d")
                        context.reset()
                        const gradient = context.createLinearGradient(
                            0, 0, width, 0
                        )
                        for (const stop of colorMapButton.modelData.stops)
                            gradient.addColorStop(stop.position, stop.color)
                        context.fillStyle = gradient
                        context.fillRect(0, 0, width, height)
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: colorMapButton.modelData.label
                    color: colorMapButton.checked
                        ? Theme.textPrimary : Theme.textSecondary
                    Layout.minimumWidth: 0
                    wrapMode: Text.Wrap
                    font.pixelSize: 12
                    font.weight: colorMapButton.checked
                        ? Font.DemiBold : Font.Normal
                }

                Text {
                    visible: colorMapButton.checked
                    text: "✓"
                    color: Theme.iconActive
                    font.pixelSize: 16
                    font.bold: true
                }
            }

            background: Rectangle {
                color: colorMapButton.checked
                    ? Theme.selectionBackground
                    : colorMapButton.hovered
                        ? Theme.controlHover : "transparent"
                border.color: colorMapButton.checked
                    ? Theme.selectionBorder : "transparent"
                border.width: 1
                radius: 5
            }
        }
    }

    Item { Layout.fillHeight: true }
}
