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
        {key: "sources", title: "数据源", subtitle: "本地与 PACS"},
        {key: "colormap", title: "伪彩", subtitle: "灰阶与 PET"},
        {key: "window", title: "窗模板", subtitle: "窗宽 / 窗位预设"},
        {key: "crosshair", title: "十字线", subtitle: "MPR 颜色与线宽"},
        {key: "corners", title: "四角信息", subtitle: "显示内容与样式"},
        {key: "scale", title: "比例尺", subtitle: "显示与颜色"},
        {key: "measurement", title: "测量与标注", subtitle: "线条、文字与箭头"},
        {key: "roi", title: "ROI 指标", subtitle: "选择显示统计项"}
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
                anchors.margins: 12
                spacing: 12
                Text { text: "工作区设置"; color: Theme.textPrimary; font.pixelSize: 18; font.bold: true; Layout.topMargin: 12 }
                Text { text: "DICOMVision"; color: Theme.textSubtle; font.pixelSize: 11 }
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
                        spacing: 6
                        Repeater {
                            model: page.categories
                            delegate: Components.AppButton {
                                id: category
                                required property var modelData
                                objectName: "settingsCategory-" + modelData.key
                                Layout.fillWidth: true
                                Layout.preferredHeight: 56
                                visible: !search.text || (modelData.title + modelData.subtitle).toLowerCase().indexOf(search.text.toLowerCase()) >= 0
                                checkable: true
                        autoExclusive: true
                                checked: page.selectedCategory === modelData.key
                                onClicked: page.settingsController.selectCategory(modelData.key)
                                baseBorderWidth: 1
                                contentItem: Column {
                                    spacing: 5
                                    Text { text: category.modelData.title; color: Theme.textPrimary; font.pixelSize: 13; font.bold: category.checked }
                                    Text { text: category.modelData.subtitle; color: Theme.textMuted; font.pixelSize: 10 }
                                }
                            }
                        }
                    }
                }
            }
        }
        Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: Theme.dividerColor }
        Loader {
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
