pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../components" as Components
import "../theme"

Rectangle {
    id: leftPanel
    objectName: "leftPanel"
    required property var panelController
    property var pacsController: null
    property var workspaceController: null
    readonly property string activeSeriesUid: panelController.activeSeriesUid
    readonly property string activeSeriesModality: panelController.activeSeriesModality
    readonly property var navigationActions: [
        {label: "打开文件夹", type: "file", icon: "nav-load-file", supported: true},
        {label: "PACS 浏览器", type: "pacs", icon: "nav-pacs", supported: true},
        {label: "2D 视图", type: "2d", icon: "nav-view-2d", supported: true},
        {label: "MPR 视图", type: "mpr", icon: "nav-view-mpr", supported: true},
        {label: "3D 视图", type: "3d", icon: "nav-view-3d", supported: true},
        {label: "平铺视图", type: "montage", icon: "nav-view-tile", supported: true},
        {label: "4D 视图", type: "4d", icon: "nav-view-4d", supported: true},
        {label: "DICOM Tag 视图", type: "tag", icon: "nav-view-tag", supported: true},
        {label: "融合视图", type: "fusion", icon: "fusion", supported: true}
    ].filter(action => action.type === "file"
        ? !leftPanel.pacsController || leftPanel.pacsController.localEnabled
        : action.type !== "pacs" || (leftPanel.pacsController && leftPanel.pacsController.pacsEnabled))
    readonly property var primaryActions: navigationActions.slice(0, 4)
    readonly property var secondaryActions: navigationActions.slice(4)
    property string selectedSource: workspaceController?.activeTabType === "pacs" ? "pacs" : "file"
    readonly property string activeSource: navigationActions.some(action => action.type === selectedSource)
        ? selectedSource : navigationActions[0].type
    readonly property int sourceCount: navigationActions.filter(action => ["file", "pacs"].includes(action.type)).length
    property string lastQuery: ""
    color: Theme.panelBackground
    border.color: Theme.borderDefault
    border.width: 1
    radius: 8
    clip: true

    function refreshRows() {
        const reset = lastQuery !== panelController.patientSearch
        const offset = reset ? 0 : seriesList.contentY
        lastQuery = panelController.patientSearch
        seriesList.model = panelController.sidebarItems
        Qt.callLater(function() {
            seriesList.contentY = Math.max(0, Math.min(offset, seriesList.contentHeight - seriesList.height))
        })
    }

    Component.onCompleted: refreshRows()
    Connections {
        target: leftPanel.panelController
        function onSidebarItemsChanged() { leftPanel.refreshRows() }
    }

    Connections {
        target: leftPanel.workspaceController
        function onActiveTabChanged() {
            if (leftPanel.workspaceController.activeTabType === "pacs")
                leftPanel.selectedSource = "pacs"
        }
    }

    component NavigationActionButton: Components.ToolbarAction {
        id: navigationAction

        required property var actionData
        readonly property bool isFileAction: actionData.type === "file"
        readonly property bool isPacsAction: actionData.type === "pacs"

        buttonObjectName: isFileAction
            ? "sidebarOpenFolder"
            : isPacsAction ? "sidebarPacs" : "openView-" + actionData.type
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.preferredWidth: 1
        Layout.minimumWidth: 0
        label: actionData.label
        shortLabel: actionData.label
        iconSize: Theme.navigationIconSize
        checked: (isFileAction || isPacsAction) && leftPanel.activeSource === actionData.type
        segmented: isFileAction || isPacsAction
        normalIconColor: segmented ? Theme.folderAccent : Theme.iconDefault
        disabledIconColor: normalIconColor
        iconName: actionData.icon
        placeholder: !actionData.supported
        actionEnabled: isFileAction
            ? !leftPanel.panelController.scanning
            : isPacsAction ? leftPanel.workspaceController !== null
            : leftPanel.activeSeriesUid !== ""
                && actionData.supported
                && (leftPanel.activeSeriesModality !== "PT"
                    || ["2d", "tag", "mpr", "fusion"].includes(actionData.type))
                && (actionData.type !== "montage" || !leftPanel.panelController.scanning)
                && (
                    actionData.type !== "4d"
                    || leftPanel.panelController.activeSeriesSupportsFourD
                )

        onTriggered: {
            if (isFileAction || isPacsAction)
                leftPanel.selectedSource = actionData.type
            if (isFileAction)
                leftPanel.panelController.openFolderDialog()
            else if (isPacsAction)
                leftPanel.workspaceController.openPacs()
            else if (actionData.type === "fusion")
                leftPanel.panelController.requestFusionView()
            else
                leftPanel.panelController.openSeriesView(
                    leftPanel.activeSeriesUid,
                    actionData.type
                )
        }

        tooltipText: actionData.label

    }

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: 12
        anchors.bottomMargin: 4
        anchors.leftMargin: 1
        anchors.rightMargin: 1
        spacing: 10

        Rectangle {
            Layout.fillWidth: true
            Layout.leftMargin: 10
            Layout.rightMargin: 10
            Layout.preferredHeight: Theme.toolbarButtonHeight * 2 + 4
            color: "transparent"

            ColumnLayout {
                anchors.fill: parent
                spacing: 4

                Item {
                    implicitHeight: Theme.toolbarButtonHeight
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Rectangle {
                        objectName: "sourceEntryGroup"
                        width: ((primaryRow.width - 3 * primaryRow.spacing) / 4) * leftPanel.sourceCount
                            + primaryRow.spacing * (leftPanel.sourceCount - 1)
                        height: parent.height
                        radius: Theme.controlRadius
                        color: Theme.folderSurface
                        border.color: Theme.selectionBorder
                        Rectangle {
                            visible: leftPanel.sourceCount === 2
                            anchors.centerIn: parent
                            width: 1
                            height: parent.height - 16
                            color: Theme.selectionBorder
                            opacity: 0.45
                        }
                    }
                    RowLayout {
                        id: primaryRow
                        anchors.fill: parent
                        spacing: 4
                        Repeater {
                            model: leftPanel.primaryActions
                            delegate: NavigationActionButton {
                                required property var modelData
                                actionData: modelData
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 4

                    Repeater {
                        model: leftPanel.secondaryActions
                        delegate: NavigationActionButton {
                            required property var modelData
                            actionData: modelData
                        }
                    }
                }
            }
        }

        Components.AppTextField {
            objectName: "sidebarPatientSearch"
            Layout.fillWidth: true
            Layout.leftMargin: 10
            Layout.rightMargin: 10
            implicitHeight: 36
            placeholderText: "搜索患者姓名 / ID"
            text: leftPanel.panelController.patientSearch
            onTextEdited: leftPanel.panelController.setPatientSearch(text)
            color: Theme.textPrimary
            placeholderTextColor: Theme.textSubtle
            selectionColor: Theme.selectionBackground
            font.pixelSize: 13
            leftPadding: 10
        }

        Text {
            Layout.leftMargin: 10
            color: Theme.textMuted
            font.pixelSize: 11
            text: "已选 " + leftPanel.panelController.selectedSeriesUids.length + " 个序列 · Cmd/Ctrl 单击多选"
        }


        ListView {
            id: seriesList
            objectName: "sidebarSeriesList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            reuseItems: true
            boundsBehavior: Flickable.StopAtBounds
            Basic.ScrollBar.vertical: Basic.ScrollBar { }

            delegate: Rectangle {
                id: entry
                required property var modelData
                readonly property bool isSeries: modelData.kind === "series"
                readonly property bool selected: isSeries && leftPanel.panelController.selectedSeriesUids.includes(modelData.seriesInstanceUid)
                objectName: isSeries ? "series-" + modelData.seriesInstanceUid : "sidebar-" + modelData.key
                width: seriesList.width
                height: isSeries ? 58 : modelData.kind === "patient" ? 30 : 26
                color: selected ? Theme.selectionBackground
                    : mouse.containsMouse ? Theme.cardBackgroundHover
                    : isSeries ? "transparent" : Theme.panelBackgroundStrong

                Rectangle {
                    width: 3
                    height: parent.height
                    visible: entry.selected
                    color: Theme.primaryColor
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: entry.modelData.kind === "study" ? 23 : 10
                    anchors.rightMargin: 26
                    spacing: leftPanel.width < 230 ? 6 : 9
                    Text {
                        visible: !entry.isSeries
                        text: entry.modelData.expanded ? "▾" : "▸"
                        color: Theme.textMuted
                        font.pixelSize: 13
                    }
                    Rectangle {
                        visible: entry.isSeries
                        Layout.preferredWidth: 16
                        Layout.preferredHeight: 16
                        radius: 8
                        color: entry.selected ? Theme.primaryStrong : "transparent"
                        border.color: entry.selected ? Theme.primaryStrong : Theme.borderStrong
                        Text {
                            anchors.centerIn: parent
                            visible: entry.selected
                            text: "✓"
                            color: Theme.textOnPrimary
                            font.pixelSize: 11
                        }
                    }
                    Rectangle {
                        visible: entry.isSeries
                        Layout.preferredWidth: 42
                        Layout.preferredHeight: 42
                        radius: 7
                        color: Theme.canvasBackground
                        border.color: Theme.borderSubtle
                        Image {
                            id: thumbnail
                            objectName: "seriesThumbnail-" + entry.modelData.seriesInstanceUid
                            anchors.fill: parent
                            anchors.margins: 3
                            source: entry.modelData.thumbnailUrl
                            fillMode: Image.PreserveAspectFit
                            smooth: true
                            mipmap: true
                            cache: false
                        }
                        Text {
                            anchors.centerIn: parent
                            visible: thumbnail.status !== Image.Ready
                            text: entry.modelData.modality || "—"
                            color: Theme.textSubtle
                            font.pixelSize: 12
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 5
                        Text {
                            Layout.fillWidth: true
                            text: entry.modelData.label
                            textFormat: Text.PlainText
                            elide: Text.ElideRight
                            font.pixelSize: entry.modelData.kind === "patient" ? 14 : 12
                            font.weight: entry.modelData.kind === "study" ? Font.Normal : Font.DemiBold
                            color: entry.modelData.kind === "study" ? Theme.textMuted : Theme.textPrimary
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: entry.isSeries && text !== ""
                            text: entry.modelData.subtitle
                            textFormat: Text.PlainText
                            elide: Text.ElideRight
                            font.pixelSize: 10
                            color: Theme.textMuted
                        }
                    }
                    Text {
                        visible: entry.isSeries
                        text: "#" + entry.modelData.dicomFileCount
                        color: entry.selected ? Theme.primaryHover : Theme.textMuted
                        font.pixelSize: 12
                    }
                }

                MouseArea {
                    id: mouse
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    cursorShape: Qt.PointingHandCursor
                    onClicked: event => {
                        if (entry.isSeries && event.button === Qt.RightButton) {
                            leftPanel.panelController.selectContextSeries(entry.modelData.seriesInstanceUid)
                            const point = entry.mapToItem(null, event.x, event.y)
                            seriesContextMenu.openFor(entry.modelData.seriesInstanceUid, point.x, point.y)
                        } else if (entry.isSeries) {
                            leftPanel.panelController.selectSeriesWithModifiers(entry.modelData.seriesInstanceUid,
                                (event.modifiers & (Qt.ControlModifier | Qt.MetaModifier)) !== 0)
                        } else if (leftPanel.panelController.patientSearch.trim() === "") {
                            leftPanel.panelController.toggleGroup(entry.modelData.key)
                        }
                    }
                    onDoubleClicked: event => {
                        if (entry.isSeries && event.button === Qt.LeftButton)
                            leftPanel.panelController.openSeriesView(entry.modelData.seriesInstanceUid, "2d")
                    }
                }
                Basic.ToolTip.visible: mouse.containsMouse
                Basic.ToolTip.delay: 900
                Basic.ToolTip.text: entry.modelData.label + (entry.modelData.subtitle ? "\n" + entry.modelData.subtitle : "")
            }

            Text {
                anchors.centerIn: parent
                visible: seriesList.count === 0
                text: leftPanel.panelController.patientSearch.trim() !== "" ? "没有匹配的患者"
                    : leftPanel.panelController.scanning ? "正在扫描 DICOM…" : "打开 DICOM 文件夹\n以查看患者和序列"
                color: Theme.textSubtle
                font.pixelSize: 12
                horizontalAlignment: Text.AlignHCenter
                lineHeight: 1.4
            }
        }
        Item {
            objectName: "sidebarSettingsFooter"
            Layout.fillWidth: true
            Layout.preferredHeight: 32
            Layout.topMargin: -6
            Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: Theme.dividerColor }
            Components.ToolbarAction {
                buttonObjectName: "sidebarSettings"
                anchors.right: parent.right
                anchors.rightMargin: 8
                anchors.bottom: parent.bottom
                width: 28
                height: 28
                label: "工作区设置"
                tooltipText: "工作区设置"
                iconName: "settings"
                iconSize: 18
                checked: leftPanel.workspaceController && leftPanel.workspaceController.activeTabType === "settings"
                visible: leftPanel.workspaceController !== null
                onTriggered: leftPanel.workspaceController.openSettings()
            }
        }
    }

    component SeriesMenuItem: Basic.MenuItem {
        id: seriesMenuItem

        required property string actionCode
        required property string iconName
        property bool actionEnabled: true
        property bool danger: false

        objectName: "seriesContextAction-" + actionCode
        enabled: actionEnabled && (leftPanel.panelController.seriesModality(seriesContextMenu.contextSeriesUid) !== "PT"
            || !["montage", "3d", "4d"].includes(actionCode))
        implicitWidth: 244
        implicitHeight: 30
        leftPadding: 9
        rightPadding: 10
        topPadding: 5
        bottomPadding: 5
        hoverEnabled: true

        contentItem: RowLayout {
            spacing: 9

            Components.AppIcon {
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                iconName: seriesMenuItem.iconName
                iconSize: 16
                iconColor: !seriesMenuItem.enabled
                    ? Theme.textDisabled
                    : seriesMenuItem.danger
                        ? Theme.dangerColor
                        : seriesMenuItem.highlighted
                            ? Theme.iconHover
                            : Theme.iconDefault
            }

            Text {
                Layout.fillWidth: true
                text: seriesMenuItem.text
                color: !seriesMenuItem.enabled
                    ? Theme.textDisabled
                    : seriesMenuItem.danger
                        ? Theme.dangerColor
                        : Theme.textPrimary
                font.pixelSize: 12
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }
        }

        background: Rectangle {
            radius: 2
            color: seriesMenuItem.enabled && seriesMenuItem.highlighted
                ? seriesMenuItem.danger
                    ? Theme.dangerSurface
                    : Theme.controlHover
                : "transparent"
        }

        onTriggered: seriesContextMenu.triggerAction(actionCode)

        Basic.ToolTip.visible: hovered && !actionEnabled
        Basic.ToolTip.delay: 350
        Basic.ToolTip.text: ["montage", "3d", "4d"].includes(actionCode)
            ? "所选序列不支持此视图" : "暂未实现"
    }

    component SeriesMenuSeparator: Basic.MenuSeparator {
        implicitHeight: 7
        topPadding: 3
        bottomPadding: 3
        contentItem: Rectangle {
            implicitHeight: 1
            color: Theme.dividerColor
        }
    }

    Basic.Menu {
        id: seriesContextMenu
        objectName: "seriesContextMenu"
        parent: Basic.Overlay.overlay
        property string contextSeriesUid: ""
        property real requestedSceneX: 0
        property real requestedSceneY: 0
        width: Math.min(252, parent.width - 16)
        padding: 4
        modal: false
        focus: true
        closePolicy: Basic.Popup.CloseOnEscape | Basic.Popup.CloseOnPressOutside
        z: 1000
        onOpened: reposition()
        onHeightChanged: {
            if (opened)
                reposition()
        }

        function reposition() {
            x = Math.max(8, Math.min(requestedSceneX, parent.width - width - 8))
            y = Math.max(8, Math.min(requestedSceneY, parent.height - height - 8))
        }

        function openFor(seriesUid, sceneX, sceneY) {
            contextSeriesUid = seriesUid
            requestedSceneX = sceneX
            requestedSceneY = sceneY
            open()
            Qt.callLater(reposition)
        }

        function triggerAction(action) {
            const seriesUid = contextSeriesUid
            close()
            if (action === "fusion") {
                leftPanel.panelController.requestFusionView()
            } else if (["2d", "mpr", "tag", "3d", "4d", "montage"].includes(action)) {
                leftPanel.panelController.openSeriesView(seriesUid, action)
            } else if (action === "directory") {
                if (!leftPanel.panelController.openSeriesDirectory(seriesUid))
                    directoryErrorDialog.open()
            } else if (action === "remove") {
                leftPanel.panelController.removeSeries(seriesUid)
                contextSeriesUid = ""
            }
        }

        background: Rectangle {
            color: Theme.elevatedBackground
            border.color: Theme.borderStrong
            border.width: 1
            radius: 3
        }

        SeriesMenuItem {
            actionCode: "2d"
            iconName: "scroll"
            text: "快速浏览"
        }
        SeriesMenuItem {
            actionCode: "montage"
            iconName: "nav-view-tile"
            text: "序列平铺"
            actionEnabled: !leftPanel.panelController.scanning
        }
        SeriesMenuItem {
            actionCode: "mpr"
            iconName: "rotate-3d"
            text: "多平面重建 (MPR)"
        }
        SeriesMenuItem {
            actionCode: "fusion"
            iconName: "fusion"
            text: "融合浏览"
        }
        SeriesMenuItem {
            actionCode: "3d"
            iconName: "rotate-3d-variant"
            text: "3D 体渲染"
        }
        SeriesMenuItem {
            actionCode: "4d"
            iconName: "cine-play"
            text: "4D 相位播放"
            actionEnabled: leftPanel.panelController.seriesSupportsFourD(
                seriesContextMenu.contextSeriesUid
            )
        }
        SeriesMenuItem {
            actionCode: "tag"
            iconName: "annotate"
            text: "DICOM 标签"
        }

        SeriesMenuSeparator { }

        SeriesMenuItem {
            actionCode: "directory"
            iconName: "folder"
            text: "在资源管理器中打开"
        }
        SeriesMenuItem {
            actionCode: "deidentify"
            iconName: "shield"
            text: "脱敏导出"
            actionEnabled: false
        }

        SeriesMenuSeparator { }

        SeriesMenuItem {
            actionCode: "remove"
            iconName: "close"
            text: "从列表中移除序列"
            danger: true
        }
    }

    FusionSeriesDialog { controller: leftPanel.panelController }

    Basic.Dialog {
        id: directoryErrorDialog
        objectName: "seriesDirectoryErrorDialog"
        parent: Basic.Overlay.overlay
        anchors.centerIn: parent
        width: 360
        height: 160
        title: "无法打开目录"
        modal: true
        standardButtons: Basic.Dialog.Ok
        contentItem: Text {
            text: "序列来源目录不存在或系统无法打开该目录。"
            color: Theme.textPrimary
            font.pixelSize: 13
            wrapMode: Text.Wrap
        }
        background: Rectangle {
            color: Theme.panelBackgroundStrong
            border.color: Theme.borderDefault
            radius: 8
        }
    }
}
