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
    required property var settingsController
    color: Theme.panelBackgroundStrong
    readonly property string selectedCategory: settingsController.activeCategory
    readonly property var categories: [
        {key: "sources", title: "数据源", subtitle: "本地与 PACS", group: "连接"},
        {key: "export", title: "导出", subtitle: "导出位置与匿名", group: "文件"},
        {key: "colormap", title: "伪彩", subtitle: "灰阶与 PET", group: "影像显示"},
        {key: "window", title: "窗模板", subtitle: "窗宽 / 窗位预设"},
        {key: "crosshair", title: "十字线", subtitle: "MPR 颜色与线宽"},
        {key: "corners", title: "四角信息", subtitle: "显示内容与样式"},
        {key: "scale", title: "比例尺", subtitle: "显示与颜色"},
        {key: "measurement", title: "测量与标注", subtitle: "线条、文字与箭头", group: "测量"},
        {key: "roi", title: "ROI 指标", subtitle: "选择显示统计项"}
    ]
    readonly property bool compactNavigation: height < 620
    property real dragWidth: -1
    readonly property real navigationLimit: Math.max(156, Math.min(300, width - 360 - 8))
    readonly property real navigationWidth: Math.min(navigationLimit,
        dragWidth >= 0 ? dragWidth : settingsController.values.layout.settingsNavigationWidth)
    RowLayout {
        anchors.fill: parent
        spacing: 0
        Rectangle {
            objectName: "settingsNavigation"
            Layout.minimumWidth: page.navigationWidth
            Layout.preferredWidth: page.navigationWidth
            Layout.maximumWidth: page.navigationWidth
            Layout.fillHeight: true
            color: Theme.panelBackground
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: page.compactNavigation ? 8 : 10
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 4
                    spacing: 3
                    Text { Layout.minimumHeight: implicitHeight; text: "工作区设置"; color: Theme.textPrimary; font.pixelSize: 15; font.bold: true }
                    Text {
                        objectName: "settingsApplicationVersion"
                        Layout.fillWidth: true
                        Layout.minimumHeight: Math.max(16, implicitHeight)
                        maximumLineCount: 1
                        verticalAlignment: Text.AlignVCenter
                        text: "Voxenra " + page.settingsController.applicationVersion
                        color: Theme.textMuted
                        font.pixelSize: 11
                        elide: Text.ElideRight
                    }
                }
                Components.AppTextField {
                    id: search
                    objectName: "settingsSearch"
                    Layout.fillWidth: true
                    placeholderText: "搜索设置"
                }
                Basic.ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentWidth: availableWidth
                    clip: true
                    ColumnLayout {
                        width: parent.width
                        spacing: page.compactNavigation ? 2 : 4
                        Repeater {
                            model: page.categories
                            delegate: ColumnLayout {
                                id: entry
                                required property var modelData
                                Layout.fillWidth: true
                                spacing: page.compactNavigation ? 2 : 4
                                visible: !search.text || (modelData.title + modelData.subtitle).toLowerCase().includes(search.text.toLowerCase())
                                Text {
                                    visible: !!entry.modelData.group && !search.text
                                    Layout.topMargin: page.compactNavigation ? 4 : 8
                                    text: entry.modelData.group ?? ""
                                    color: Theme.textSubtle; font.pixelSize: 10
                                }
                                Components.AppButton {
                                    id: category
                                    objectName: "settingsCategory-" + entry.modelData.key
                                    Layout.fillWidth: true
                                    Layout.minimumHeight: page.compactNavigation ? 28 : 34
                                    Layout.preferredHeight: Layout.minimumHeight
                                    Layout.maximumHeight: Layout.minimumHeight
                                    topPadding: 4
                                    bottomPadding: 4
                                    checked: page.selectedCategory === entry.modelData.key
                                    onClicked: page.settingsController.selectCategory(entry.modelData.key)
                                    Accessible.name: entry.modelData.title
                                    contentItem: Text {
                                        text: entry.modelData.title; color: category.checked ? Theme.textPrimary : Theme.textSecondary
                                        font.pixelSize: 13; font.weight: category.checked ? Font.DemiBold : Font.Normal
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    background: Rectangle {
                                        radius: 4
                                        color: category.checked ? Theme.selectionBackground : category.hovered ? Theme.controlHover : "transparent"
                                        border.width: category.visualFocus ? 1 : 0; border.color: Theme.focusBorder
                                        Rectangle { width: 3; height: 16; radius: 1; anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter; color: Theme.primaryColor; visible: category.checked }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        Components.WidthResizeHandle {
            objectName: "settingsNavigationResizeHandle"
            Layout.preferredWidth: 8
            Layout.fillHeight: true
            currentWidth: page.navigationWidth
            minimumWidth: 156
            maximumWidth: page.navigationLimit
            onWidthDragged: value => page.dragWidth = value
            onWidthCommitted: value => {
                page.settingsController.setValue("layout", "settingsNavigationWidth", Math.round(value))
                page.dragWidth = -1
            }
        }
        Loader {
            Layout.minimumWidth: 360
            Layout.fillWidth: true
            Layout.fillHeight: true
            sourceComponent: page.selectedCategory === "sources" ? sourcesComponent : displayComponent
        }
    }
    Component { id: sourcesComponent; DataSourcesPage { pacsController: page.pacsController } }
    Component {
        id: displayComponent
        DisplaySettingsPage {
            settingsController: page.settingsController
            category: page.selectedCategory
            title: page.categories.find(item => item.key === page.selectedCategory)?.title ?? ""
        }
    }
}
