pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"

Item {
    id: page
    required property var settingsController
    required property string category
    required property string title
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 10
        RowLayout {
            Layout.fillWidth: true
            Text { Layout.fillWidth: true; text: page.title; color: Theme.textPrimary; font.pixelSize: 18; font.bold: true }
            Components.AppButton { objectName: "resetDisplaySettings"; text: "恢复默认"; compact: true; normalColor: "transparent"; baseBorderWidth: 1; onClicked: page.settingsController.resetSection(page.category) }
        }
        Text {
            Layout.fillWidth: true
            text: page.category === "window" ? "保存后同步到调窗面板；选择模板即可应用。" : "修改即时生效，并自动保存到本机。"
            color: Theme.textMuted
            font.pixelSize: 12
            wrapMode: Text.Wrap
        }
        Text {
            objectName: "settingsError"
            Layout.fillWidth: true
            visible: text.length > 0
            text: page.settingsController.message
            color: Theme.dangerColor
            wrapMode: Text.Wrap
        }
        Basic.ScrollView {
            id: scroll
            objectName: "displaySettingsScroll"
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: availableWidth
            rightPadding: 12
            clip: true
            Basic.ScrollBar.vertical: Components.AppScrollBar {}
            Loader {
                id: content
                width: scroll.availableWidth
                sourceComponent: ({colormap: colorsPage, window: windowsPage, crosshair: crosshairPage,
                    corners: cornersPage, scale: scalePage, measurement: measurementPage, roi: roiPage})[page.category]
            }
        }
    }
    Component { id: colorsPage; ColorMapsPage { settingsController: page.settingsController } }
    Component { id: windowsPage; WindowTemplatesPage { settingsController: page.settingsController } }
    Component { id: crosshairPage; CrosshairSettingsPage { settingsController: page.settingsController } }
    Component { id: cornersPage; CornerSettingsPage { settingsController: page.settingsController } }
    Component { id: scalePage; ScaleSettingsPage { settingsController: page.settingsController } }
    Component { id: measurementPage; MeasurementSettingsPage { settingsController: page.settingsController } }
    Component { id: roiPage; RoiSettingsPage { settingsController: page.settingsController } }
}
