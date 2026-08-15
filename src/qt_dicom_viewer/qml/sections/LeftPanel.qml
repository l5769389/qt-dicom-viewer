pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts

Rectangle {
    id: leftPanel

    required property var panelController

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

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 1

                Text {
                    text: "DICOM Series"
                    color: "#f2f5f8"
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }

                Text {
                    text: seriesList.count + " series"
                    color: "#7f8997"
                    font.pixelSize: 11
                }
            }

            Basic.Button {
                id: openButton
                text: "Open"
                implicitHeight: 34

                contentItem: Text {
                    text: openButton.text
                    color: "#f7fbff"
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    color: openButton.down ? "#3977ad"
                                           : openButton.hovered ? "#438bc7"
                                                                : "#347bb7"
                    radius: 5
                }

                onClicked: leftPanel.panelController.openFolderDialog()
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
            model: leftPanel.panelController.seriesItems

            ScrollBar.vertical: Basic.ScrollBar {
                policy: ScrollBar.AsNeeded
            }

            delegate: Rectangle {
                id: seriesDelegate

                required property int index
                required property var modelData

                width: ListView.view.width
                implicitHeight: seriesColumn.implicitHeight + 24
                radius: 6
                color: ListView.isCurrentItem
                       ? "#27394b"
                       : mouseArea.containsMouse ? "#252b34" : "#20252d"
                border.color: ListView.isCurrentItem ? "#4f9ad2" : "#303743"
                border.width: 1

                Rectangle {
                    visible: ListView.isCurrentItem
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: 3
                    color: "#58a8df"
                    radius: 2
                }

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
                                text: seriesDelegate.modelData.fileCount + " files"
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
                        leftPanel.panelController.loadSeries(
                            seriesDelegate.modelData.seriesInstanceUid
                        )
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                visible: seriesList.count === 0
                text: "Open a DICOM folder\nto view available series"
                color: "#66717f"
                font.pixelSize: 12
                horizontalAlignment: Text.AlignHCenter
                lineHeight: 1.35
            }
        }
    }
}
