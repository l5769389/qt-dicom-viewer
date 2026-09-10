pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../../components" as Components
import "../components" as Controls
import "../../../theme"

ColumnLayout {
    id: playbackPanel
    objectName: "fourDPlaybackPanel"

    required property var tabController

    implicitHeight: Theme.toolbarButtonHeight + 8 + spacing + phaseCard.implicitHeight
    spacing: 8

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: Theme.toolbarButtonHeight + 8
        radius: 8
        color: Theme.controlBackground
        border.width: 1
        border.color: fpsSlider.pressed
            ? Theme.selectionBorder
            : Theme.controlBorder

        Behavior on border.color {
            ColorAnimation { duration: 100 }
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 9
            anchors.rightMargin: 5
            anchors.topMargin: 4
            anchors.bottomMargin: 4
            spacing: 7

            Text {
                text: "FPS"
                color: Theme.textSecondary
                font.pixelSize: 12
                font.weight: Font.DemiBold
            }

            Basic.Slider {
                id: fpsSlider
                objectName: "fpsSlider"

                Layout.fillWidth: true
                Layout.preferredHeight: 30
                from: 1
                to: 15
                stepSize: 1
                snapMode: Basic.Slider.SnapAlways
                value: playbackPanel.tabController
                    ? playbackPanel.tabController.fps
                    : 2

                onMoved: {
                    playbackPanel.tabController?.setFps(
                        Math.round(value)
                    )
                }

                Basic.ToolTip.visible: hovered || pressed
                Basic.ToolTip.delay: 250
                Basic.ToolTip.text: Math.round(value) + " FPS"

                background: Rectangle {
                    x: fpsSlider.leftPadding
                    y: fpsSlider.topPadding
                        + fpsSlider.availableHeight / 2 - height / 2
                    width: fpsSlider.availableWidth
                    height: 4
                    radius: 2
                    color: Theme.controlBorder

                    Rectangle {
                        width: fpsSlider.visualPosition * parent.width
                        height: parent.height
                        radius: parent.radius
                        color: Theme.primaryColor
                    }
                }

                handle: Rectangle {
                    x: fpsSlider.leftPadding
                        + fpsSlider.visualPosition
                        * (fpsSlider.availableWidth - width)
                    y: fpsSlider.topPadding
                        + fpsSlider.availableHeight / 2 - height / 2
                    implicitWidth: 13
                    implicitHeight: 13
                    radius: width / 2
                    color: fpsSlider.pressed
                        ? Theme.primaryHover
                        : Theme.primaryColor
                    border.width: 2
                    border.color: Theme.panelBackgroundStrong
                }
            }

            Text {
                objectName: "fpsValue"
                Layout.preferredWidth: 20
                text: playbackPanel.tabController
                    ? playbackPanel.tabController.fps
                    : 2
                color: Theme.textPrimary
                font.pixelSize: 14
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignHCenter
            }

            Controls.ToolActionButton {
                objectName: "phasePlaybackButton"
                Layout.preferredWidth: 44
                checked: playbackPanel.tabController ? playbackPanel.tabController.playing : false
                label: checked ? "暂停" : "播放"
                iconName: checked ? "cine-pause" : "cine-play"
                onClicked: playbackPanel.tabController?.togglePlayback()
            }
        }
    }

    Rectangle {
        id: phaseCard
        Layout.fillWidth: true
        implicitHeight: phaseControls.implicitHeight + 18
        Layout.minimumHeight: implicitHeight
        radius: Theme.controlRadius
        color: Theme.cardBackground
        border.width: 1
        border.color: Theme.borderDefault

        ColumnLayout {
            id: phaseControls
            anchors.fill: parent
            anchors.margins: 9
            spacing: 5

            RowLayout {
                Layout.fillWidth: true

                Text {
                    text: "相位"
                    color: Theme.textSecondary
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                }

                Item { Layout.fillWidth: true }

                Text {
                    objectName: "phasePositionLabel"
                    text: playbackPanel.tabController
                        ? (playbackPanel.tabController.currentPhaseIndex + 1)
                            + " / "
                            + playbackPanel.tabController.phaseCount
                        : "0 / 0"
                    color: Theme.textMuted
                    font.pixelSize: 11
                }
            }

            Basic.Slider {
                id: phaseSlider
                objectName: "phaseSlider"

                Layout.fillWidth: true
                from: 1
                to: Math.max(
                    1,
                    playbackPanel.tabController
                        ? playbackPanel.tabController.phaseCount
                        : 1
                )
                stepSize: 1
                snapMode: Basic.Slider.SnapAlways
                value: playbackPanel.tabController
                    ? playbackPanel.tabController.currentPhaseIndex + 1
                    : 1

                onMoved: {
                    playbackPanel.tabController?.setPhaseIndex(
                        Math.round(value) - 1
                    )
                }

                Basic.ToolTip.visible: hovered || pressed
                Basic.ToolTip.delay: 250
                Basic.ToolTip.text: "Phase " + Math.round(value)

                background: Rectangle {
                    x: phaseSlider.leftPadding
                    y: phaseSlider.topPadding
                        + phaseSlider.availableHeight / 2 - height / 2
                    width: phaseSlider.availableWidth
                    height: 6
                    radius: 3
                    color: Theme.controlBorder

                    Rectangle {
                        width: phaseSlider.visualPosition * parent.width
                        height: parent.height
                        radius: parent.radius
                        color: Theme.primaryStrong
                    }
                }

                handle: Rectangle {
                    x: phaseSlider.leftPadding
                        + phaseSlider.visualPosition
                        * (phaseSlider.availableWidth - width)
                    y: phaseSlider.topPadding
                        + phaseSlider.availableHeight / 2 - height / 2
                    implicitWidth: 14
                    implicitHeight: 14
                    radius: width / 2
                    color: Theme.primaryColor
                    border.width: 2
                    border.color: Theme.panelBackgroundStrong
                }
            }

            GridView {
                id: phaseGrid
                objectName: "phaseGrid"

                Layout.fillWidth: true
                Layout.preferredHeight: Math.max(1, Math.min(4, Math.ceil(count / columnCount))) * cellHeight
                Layout.minimumHeight: Layout.preferredHeight
                clip: true
                readonly property int columnCount: 5
                cellWidth: Math.max(0, width - 8) / columnCount
                cellHeight: 39
                model: playbackPanel.tabController
                    ? playbackPanel.tabController.phaseItems
                    : []

                delegate: Components.AppButton {
                    id: phaseButton

                    required property var modelData

                    objectName: "phaseButton-" + modelData.index
                    width: phaseGrid.cellWidth - 4
                    height: phaseGrid.cellHeight - 4
                    checked: playbackPanel.tabController
                        && playbackPanel.tabController.currentPhaseIndex
                            === modelData.index

                    onClicked: {
                        playbackPanel.tabController?.setPhaseIndex(
                            modelData.index
                        )
                    }

                    contentItem: Text {
                        text: phaseButton.modelData.label
                        color: phaseButton.checked
                            ? Theme.textPrimary
                            : Theme.textMuted
                        font.pixelSize: 13
                        font.weight: phaseButton.checked
                            ? Font.DemiBold
                            : Font.Normal
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    normalColor: Theme.panelBackgroundStrong
                    activeColor: Theme.successSurface
                    activeHoverColor: Qt.lighter(Theme.successSurface, 1.25)
                    activePressedColor: Qt.darker(Theme.successSurface, 1.2)
                    activeBorderColor: Theme.successColor
                    baseBorderWidth: 1
                    baseBorderColor: Theme.borderSubtle
                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.top: parent.top
                        anchors.topMargin: 4
                        width: 6; height: 6; radius: 3
                        color: phaseButton.checked ? Theme.successColor : Theme.textDisabled
                    }
                }

                Basic.ScrollBar.vertical: Components.AppScrollBar {
                    id: phaseScrollbar
                    policy: phaseGrid.contentHeight > phaseGrid.height
                        ? Basic.ScrollBar.AsNeeded
                        : Basic.ScrollBar.AlwaysOff
                }
            }
        }
    }
}
