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
        }
        ListElement {
            label: "MPR"
            tabType: "mpr"
            supported: true
        }
        ListElement {
            label: "3D"
            tabType: "3d"
            supported: false
        }
        ListElement {
            label: "4D"
            tabType: "4d"
            supported: false
        }
        ListElement {
            label: "Tag"
            tabType: "tag"
            supported: false
        }
    }

    color: "#1b1f26"
    border.color: "#303744"
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
                color: "#f0f4f8"
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

            color: "#171c23"
            border.color: "#2b333e"
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
                    normalColor: "#245d7b"
                    hoverColor: "#2e789e"
                    pressedColor: "#1c4a63"
                    disabledColor: "#1d3c50"
                    focusBorderColor: "#83d1f2"

                    ToolTip.visible: hovered
                    ToolTip.delay: 450
                    ToolTip.text: "打开 DICOM 文件夹"

                    onClicked: leftPanel.panelController.openFolderDialog()
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 22
                    color: "#303946"
                }

                Repeater {
                    model: viewTypeModel

                    delegate: Components.AppButton {
                        required property string label
                        required property string tabType
                        required property bool supported

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
                        hoverColor: "#263442"
                        pressedColor: "#1d2a36"
                        activeColor: "#2a455b"
                        disabledColor: "transparent"
                        enabled: seriesList.currentIndex >= 0 && supported

                        ToolTip.visible: hovered
                        ToolTip.delay: 450
                        ToolTip.text: supported
                            ? "以 " + label + " 方式打开"
                            : label + " 暂未实现"

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
            color: "#2c323d"
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
                    readonly property bool isActive: leftPanel.activeSeriesUid === seriesDelegate.modelData.seriesInstanceUid

                width: ListView.view.width
                implicitHeight: seriesColumn.implicitHeight + 24
                height: implicitHeight
                radius: 6
                color: isActive
                    ? Theme.activeColor
                    : mouseArea.containsMouse
                        ? Theme.hoverColor
                        : "#20252d"
                border.color: isActive
                    ? "#4f9ad2"
                    : "#303743"
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
                            color: "#eef3f7"
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                        }

                        Rectangle {
                            implicitWidth: fileCountText.implicitWidth + 12
                            implicitHeight: 22
                            radius: 11
                            color: "#18202a"

                            Text {
                                id: fileCountText
                                anchors.centerIn: parent
                                text: seriesDelegate.modelData.dicomFileCount
                                    + " files"
                                color: "#91b9d6"
                                font.pixelSize: 10
                            }
                        }
                    }

                    Text {
                        width: parent.width
                        text: seriesDelegate.modelData.seriesInstanceUid
                        color: "#8994a3"
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
                color: "#66717f"
                font.pixelSize: 12
                horizontalAlignment: Text.AlignHCenter
                lineHeight: 1.35
            }
        }
    }
}
