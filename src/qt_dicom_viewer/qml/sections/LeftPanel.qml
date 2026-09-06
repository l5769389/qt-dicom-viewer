pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../components" as Components
import "../theme"

Rectangle {
    id: leftPanel

    required property var panelController

    property string activeSeriesUid: ""

    ListModel {
        id: viewTypeModel

        ListElement {
            label: "2D"
            tabType: "2d"
            supported: true
            requiresCompleteScan: false
        }
        ListElement {
            label: "平铺"
            tabType: "montage"
            supported: true
            requiresCompleteScan: true
        }
        ListElement {
            label: "MPR"
            tabType: "mpr"
            supported: true
            requiresCompleteScan: false
        }
        ListElement {
            label: "3D"
            tabType: "3d"
            supported: false
            requiresCompleteScan: false
        }
        ListElement {
            label: "4D"
            tabType: "4d"
            supported: false
            requiresCompleteScan: false
        }
        ListElement {
            label: "Tag"
            tabType: "tag"
            supported: false
            requiresCompleteScan: false
        }
    }

    color: Theme.panelBackground
    border.color: Theme.borderDefault
    border.width: 1
    radius: 8

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Image {
                Layout.preferredWidth: 26
                Layout.preferredHeight: 26

                source: Qt.resolvedUrl(
                    "../assets/brand/dicomvision-mark.png"
                )
                sourceSize.width: 52
                sourceSize.height: 52
                fillMode: Image.PreserveAspectFit
                mipmap: true
            }

            Text {
                text: "DICOM Vision"
                color: Theme.textPrimary
                font.pixelSize: 15
                font.weight: Font.DemiBold
            }

            Item {
                Layout.fillWidth: true
            }

        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 40

            color: Theme.panelBackgroundStrong
            border.color: Theme.borderSubtle
            border.width: 1
            radius: 7

            RowLayout {
                anchors.fill: parent
                anchors.margins: 3
                spacing: 3

                Components.AppButton {
                    Layout.preferredWidth: 36
                    Layout.fillHeight: true

                    compact: true
                    momentary: true
                    minimumButtonWidth: 36
                    iconSize: 19
                    icon.source: Qt.resolvedUrl(
                        "../assets/icons/open-folder.svg"
                    )
                    normalColor: Theme.primaryButtonBackground
                    hoverColor: Theme.primaryButtonHover
                    pressedColor: Theme.primaryButtonPressed
                    disabledColor: Theme.primaryButtonDisabled
                    focusBorderColor: Theme.primaryButtonBorder

                    ToolTip.visible: hovered
                    ToolTip.delay: 450
                    ToolTip.text: "打开 DICOM 文件夹"

                    onClicked: leftPanel.panelController.openFolderDialog()
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 22
                    color: Theme.dividerColor
                }

                Repeater {
                    model: viewTypeModel

                    delegate: Components.AppButton {
                        required property string label
                        required property string tabType
                        required property bool supported
                        required property bool requiresCompleteScan

                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.preferredWidth: 1
                        Layout.minimumWidth: 0

                        compact: true
                        momentary: true
                        minimumButtonWidth: 0
                        text: label
                        fontPixelSize: tabType === "mpr" ? 11 : 12
                        normalColor: "transparent"
                        hoverColor: Theme.controlHover
                        pressedColor: Theme.controlPressed
                        activeColor: Theme.selectionBackground
                        disabledColor: "transparent"
                        enabled: seriesList.currentIndex >= 0
                            && supported
                            && (!requiresCompleteScan
                                || !leftPanel.panelController.scanning)

                        ToolTip.visible: hovered
                        ToolTip.delay: 450
                        ToolTip.text: !supported
                            ? label + " 暂未实现"
                            : requiresCompleteScan
                                && leftPanel.panelController.scanning
                                ? "等待 DICOM 扫描完成后打开平铺"
                                : "以 " + label + " 方式打开"

                        onClicked: {
                            if (leftPanel.activeSeriesUid === "") {
                                return
                            }
                            leftPanel.panelController.openSeriesView(
                                leftPanel.activeSeriesUid,
                                tabType
                            )
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: Theme.dividerColor
        }

        ListView {
            id: seriesList

            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 8
            currentIndex: -1
            model: leftPanel.panelController.seriesItems

            ScrollBar.vertical: Basic.ScrollBar
            {
                policy: ScrollBar.AsNeeded
            }

            delegate: Rectangle {
                id: seriesDelegate

                required property int index
                required property var modelData
                readonly property bool isActive:
                    leftPanel.activeSeriesUid
                        === seriesDelegate.modelData.seriesInstanceUid

                width: ListView.view.width
                implicitHeight: seriesColumn.implicitHeight + 24
                height: implicitHeight
                radius: 6
                color: isActive
                    ? Theme.selectionBackground
                    : mouseArea.containsMouse
                        ? Theme.cardBackgroundHover
                        : Theme.cardBackground
                border.color: isActive
                    ? Theme.selectionBorder
                    : Theme.borderDefault
                border.width: 1

                // Rectangle {
                //     visible: seriesDelegate.isActive
                //     anchors.left: parent.left
                //     anchors.top: parent.top
                //     anchors.bottom: parent.bottom
                //     width: 3
                //     color: "#58a8df"
                //     radius: 2
                // }

                Column {
                    id: seriesColumn

                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 12
                    spacing: 6

                    RowLayout {
                        width: parent.width
                        spacing: 6

                        Text {
                            Layout.fillWidth: true
                            text: "Series " + (seriesDelegate.index + 1)
                            color: Theme.textPrimary
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                        }

                        Rectangle {
                            implicitWidth: fileCountText.implicitWidth + 12
                            implicitHeight: 22
                            radius: 11
                            color: Theme.secondarySoft

                            Text {
                                id: fileCountText
                                anchors.centerIn: parent
                                text: seriesDelegate.modelData.dicomFileCount
                                    + " files"
                                color: Theme.primaryHover
                                font.pixelSize: 10
                            }
                        }
                    }

                    Text {
                        width: parent.width
                        text: seriesDelegate.modelData.seriesInstanceUid
                        color: Theme.textMuted
                        font.pixelSize: 10
                        elide: Text.ElideMiddle
                        maximumLineCount: 1
                    }
                }

                MouseArea {
                    id: mouseArea

                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor

                    onClicked: {
                        seriesList.currentIndex = seriesDelegate.index
                        leftPanel.activeSeriesUid = seriesDelegate.modelData.seriesInstanceUid
                    }

                    onDoubleClicked: {
                        leftPanel.panelController.openSeriesView(
                            seriesDelegate.modelData.seriesInstanceUid,
                            '2d'
                        )
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                visible: seriesList.count === 0
                text: "打开 DICOM 文件夹\n以查看可用序列"
                color: Theme.textSubtle
                font.pixelSize: 12
                horizontalAlignment: Text.AlignHCenter
                lineHeight: 1.35
            }
        }
    }
}
