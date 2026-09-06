pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"

Rectangle {
    id: page
    objectName: "settingsPage"
    required property var pacsController
    color: Theme.panelBackgroundStrong
    property string selectedCategory: "sources"
    // Each category maps to a separate settings page.
    readonly property var categories: [
        {
            key: "sources",
            title: "数据源",
            subtitle: "本地与 PACS"
        }
    ]

    RowLayout {
        anchors.fill: parent
        spacing: 0
        Rectangle {
            Layout.preferredWidth: page.width < 800 ? 152 : 192
            Layout.fillHeight: true
            color: Theme.panelBackground
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 8
                Text {
                    text: "工作区设置"
                    color: Theme.textPrimary
                    font.pixelSize: 18
                    font.bold: true
                    Layout.topMargin: 12
                }
                Text {
                    text: "DICOMVision"
                    color: Theme.textSubtle
                    font.pixelSize: 11
                    Layout.bottomMargin: 24
                }
                Repeater {
                    model: page.categories
                    delegate: Rectangle {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredHeight: 66
                        color: page.selectedCategory === modelData.key ? Theme.selectionBackground : Theme.controlBackground
                        border.color: page.selectedCategory === modelData.key ? Theme.selectionBorder : Theme.borderDefault
                        radius: 7
                        Rectangle {
                            width: 3
                            height: 28
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            color: Theme.primaryColor
                        }
                        TapHandler {
                            onTapped: page.selectedCategory = modelData.key
                        }
                        Column {
                            anchors.centerIn: parent
                            width: parent.width - 26
                            spacing: 6
                            Text {
                                text: modelData.title
                                color: Theme.textPrimary
                                font.pixelSize: 14
                                font.bold: true
                            }
                            Text {
                                text: modelData.subtitle
                                color: Theme.textMuted
                                font.pixelSize: 11
                            }
                        }
                    }
                }
                Item {
                    Layout.fillHeight: true
                }
            }
        }
        Rectangle {
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            color: Theme.dividerColor
        }
        Loader {
            Layout.fillWidth: true
            Layout.fillHeight: true
            sourceComponent: page.selectedCategory === "sources" ? sourcesComponent : null
        }
    }
    Component {
        id: sourcesComponent
        DataSourcesPage {
            pacsController: page.pacsController
        }
    }
}
