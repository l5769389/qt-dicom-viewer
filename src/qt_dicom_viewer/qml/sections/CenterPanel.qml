pragma
ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts

Rectangle {
    id: centerPanel

    required property var workspaceController
    readonly property bool hasTabs: workspaceController.tabs.length > 0
    readonly property int tabWidth: 180
    readonly property var activeViewport:
        workspaceController.activeViewports.length > 0
            ? workspaceController.activeViewports[0]
            : null
    readonly property var overlay:
        activeViewport ? activeViewport.overlayInfo : ({})

    function overlayValue(key) {
        const value = overlay[key]
        return value === undefined || value === null || value === ""
            ? "--" : value
    }

    component OverlayText: Text {
        visible: centerPanel.activeViewport !== null
        color: "#f2f5f8"
        font.pixelSize: 12
        font.weight: Font.DemiBold
        font.letterSpacing: 0.15
        lineHeight: 1.28
        style: Text.Outline
        styleColor: "#cc000000"
        wrapMode: Text.Wrap
        z: 2
    }

    color: "#15191f"
    border.color: "#303744"
    border.width: 1
    radius: 8
    clip: true

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Basic.TabBar {
            id: workspaceTabs

            Layout.fillWidth: true
            Layout.preferredHeight: 44
            spacing: 2

            background: Rectangle {
                color: "#1d222a"

                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 1
                    color: "#303744"
                }
            }

            Repeater {
                model: centerPanel.workspaceController.tabs

                delegate: Basic.TabButton
                {
                    required property var modelData

                    id: tabButton
                    width: centerPanel.tabWidth
                    implicitWidth: centerPanel.tabWidth
                    implicitHeight: 44
                    checked: tabButton.modelData.tabId
                        === centerPanel.workspaceController.activeTabId

                    onClicked: {
                        centerPanel.workspaceController.activateTabId(
                            tabButton.modelData.tabId
                        )
                    }

                    contentItem: RowLayout {
                        id: tabContent
                        spacing: 8

                        Text {
                            Layout.fillWidth: true
                            text: tabButton.modelData.tabLabel
                            color: tabButton.checked ? "#f4f8fb" : "#9aa5b3"
                            font.pixelSize: 12
                            font.weight: tabButton.checked
                                ? Font.DemiBold : Font.Normal
                            elide: Text.ElideRight
                            verticalAlignment: Text.AlignVCenter
                        }

                        Basic.ToolButton {
                            id: closeButton
                            text: "×"
                            implicitWidth: 24
                            implicitHeight: 24

                            contentItem: Text {
                                text: closeButton.text
                                color: closeButton.hovered ? "#ffffff" : "#808b98"
                                font.pixelSize: 16
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }

                            background: Rectangle {
                                color: closeButton.hovered ? "#3b424d" : "transparent"
                                radius: 4
                            }

                            onClicked: {
                                centerPanel.workspaceController.closeTab(
                                    tabButton.modelData.tabId
                                )
                            }
                        }
                    }

                    background: Rectangle {
                        color: tabButton.checked
                            ? "#272e38"
                            : tabButton.hovered ? "#232933" : "transparent"

                        Rectangle {
                            visible: tabButton.checked
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            height: 2
                            color: "#58a8df"
                        }
                    }
                }
            }
        }

        Rectangle {
            id: viewportArea

            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 8
            color: "#080a0d"
            border.color: "#272d36"
            border.width: 1
            radius: 6
            clip: true

            Image {
                id: imageView
                anchors.fill: parent
                anchors.margins: 8
                source: centerPanel.activeViewport
                    ? centerPanel.activeViewport.imageSource : ""
                fillMode: Image.PreserveAspectFit
                smooth: true
                cache: false
            }

            Column {
                anchors.centerIn: parent
                spacing: 6
                visible: !centerPanel.hasTabs

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "No viewport open"
                    color: "#778392"
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Select a series from the left panel"
                    color: "#505a67"
                    font.pixelSize: 12
                }
            }

            OverlayText {
                id: topLeftText
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.margins: 14
                width: Math.min(implicitWidth, viewportArea.width * 0.46)
                text: centerPanel.overlayValue("manufacturer")
                    + "\n" + centerPanel.overlayValue("seriesDescription")
                    + "\nLocation: "
                    + centerPanel.overlayValue("sliceLocation")
                    + "\nSlice: "
                    + centerPanel.overlayValue("sliceIndex")
                    + " / " + centerPanel.overlayValue("sliceCount")
            }

            OverlayText {
                id: topRightText
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 14
                width: Math.min(implicitWidth, viewportArea.width * 0.46)
                horizontalAlignment: Text.AlignRight
                text: "Patient: " + centerPanel.overlayValue("patientName")
                    + "\nID: " + centerPanel.overlayValue("patientId")
            }

            OverlayText {
                id: bottomLeftText
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                anchors.margins: 14
                width: Math.min(implicitWidth, viewportArea.width * 0.46)
                text: "kV: " + centerPanel.overlayValue("kvp")
                    + "   mA: " + centerPanel.overlayValue("tubeCurrentMa")
                    + "\nThickness: "
                    + centerPanel.overlayValue("sliceThickness") + " mm"
                    + "\nWL: " + centerPanel.overlayValue("windowCenter")
                    + "   WW: " + centerPanel.overlayValue("windowWidth")
            }

            OverlayText {
                id: bottomRightText
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: 14
                width: Math.min(implicitWidth, viewportArea.width * 0.46)
                horizontalAlignment: Text.AlignRight
                text: "X: " + centerPanel.overlayValue("cursorX")
                    + "   Y: " + centerPanel.overlayValue("cursorY")
                    + "\nCT: " + centerPanel.overlayValue("pixelValue")
                    + " HU"
            }
        }
    }
}
