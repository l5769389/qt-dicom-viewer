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
    readonly property string activeSeriesUid: panelController.activeSeriesUid
    readonly property string activeSeriesModality: panelController.activeSeriesModality
    readonly property var viewTypes: [
        {label: "2D", type: "2d", supported: true},
        {label: "MPR", type: "mpr", supported: true},
        {label: "融合", type: "fusion", supported: true},
        {label: "3D", type: "3d", supported: true},
        {label: "4D", type: "4d", supported: false},
        {label: "Tag", type: "tag", supported: true}
    ]
    readonly property var contextActions: [
        {code: "2d", badge: "2D", label: "快速浏览", description: "二维浏览", supported: true, danger: false, separatorBefore: false},
        {code: "tile", badge: "平铺", label: "序列平铺", description: "连续显示全部二维切片", supported: false, danger: false, separatorBefore: false},
        {code: "mpr", badge: "MPR", label: "MPR", description: "多平面重建", supported: true, danger: false, separatorBefore: false},
        {code: "fusion", badge: "PET/CT", label: "融合浏览", description: "选择 CT 与 PET 进行融合", supported: true, danger: false, separatorBefore: false},
        {code: "3d", badge: "3D", label: "3D", description: "体渲染", supported: true, danger: false, separatorBefore: false},
        {code: "4d", badge: "4D", label: "4D", description: "呼吸相位播放", supported: false, danger: false, separatorBefore: false},
        {code: "tag", badge: "TAG", label: "TAG", description: "DICOM 标签", supported: true, danger: false, separatorBefore: false},
        {code: "directory", badge: "DIR", label: "在资源管理器中打开", description: "打开此序列的来源目录", supported: true, danger: false, separatorBefore: true},
        {code: "deidentify", badge: "DEID", label: "脱敏导出", description: "生成脱敏 DICOM 副本", supported: false, danger: false, separatorBefore: false},
        {code: "remove", badge: "DEL", label: "从列表中移除序列", description: "", supported: true, danger: true, separatorBefore: true}
    ]
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

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: 12
        anchors.bottomMargin: 8
        anchors.leftMargin: 1
        anchors.rightMargin: 1
        spacing: 10

        Rectangle {
            Layout.fillWidth: true
            Layout.leftMargin: 10
            Layout.rightMargin: 10
            Layout.preferredHeight: 40
            color: "transparent"
            RowLayout {
                anchors.fill: parent
                spacing: 4
                Components.AppButton {
                    objectName: "sidebarOpenFolder"
                    Layout.preferredWidth: leftPanel.width < 230 ? 30 : 34
                    Layout.fillHeight: true
                    compact: true
                    momentary: true
                    minimumButtonWidth: leftPanel.width < 230 ? 30 : 34
                    iconSize: 19
                    icon.source: Qt.resolvedUrl("../assets/icons/open-folder.svg")
                    normalColor: Theme.controlBackground
                    hoverColor: Theme.controlHover
                    pressedColor: Theme.controlPressed
                    baseBorderWidth: 1
                    baseBorderColor: Theme.borderDefault
                    enabled: !leftPanel.panelController.scanning
                    onClicked: leftPanel.panelController.openFolderDialog()
                    Basic.ToolTip.visible: hovered
                    Basic.ToolTip.delay: 450
                    Basic.ToolTip.text: "打开 DICOM 文件夹"
                }
                Repeater {
                    model: leftPanel.viewTypes
                    delegate: Components.AppButton {
                        required property var modelData
                        objectName: "openView-" + modelData.type
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.preferredWidth: 1
                        Layout.minimumWidth: 0
                        compact: true
                        momentary: true
                        minimumButtonWidth: 0
                        text: modelData.label
                        fontPixelSize: leftPanel.width < 230 ? 10 : modelData.type === "mpr" ? 11 : 12
                        leftPadding: leftPanel.width < 230 ? 3 : 6
                        rightPadding: leftPadding
                        normalColor: Theme.controlBackground
                        disabledColor: Theme.canvasBackground
                        baseBorderWidth: 1
                        baseBorderColor: Theme.borderDefault
                        enabled: leftPanel.activeSeriesUid !== ""
                            && modelData.supported
                            && (leftPanel.activeSeriesModality !== "PT"
                                || modelData.type === "2d"
                                || ["tag", "mpr", "fusion"].includes(modelData.type))
                        onClicked: modelData.type === "fusion"
                            ? leftPanel.panelController.requestFusionView()
                            : leftPanel.panelController.openSeriesView(leftPanel.activeSeriesUid, modelData.type)
                        Basic.ToolTip.visible: hovered
                        Basic.ToolTip.delay: 450
                        Basic.ToolTip.text: leftPanel.activeSeriesModality === "PT"
                            && ["3d", "4d"].includes(modelData.type)
                            ? "暂不支持 PET 体绘制或动态浏览"
                            : modelData.supported
                            ? "以 " + modelData.label + " 方式打开"
                            : modelData.label + " 暂未实现"
                    }
                }
            }
        }

        Basic.TextField {
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
            background: Rectangle {
                color: Theme.canvasBackground
                border.color: parent.activeFocus ? Theme.focusBorder : Theme.borderDefault
                radius: 6
            }
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
    }

    Basic.Popup {
        id: seriesContextMenu
        objectName: "seriesContextMenu"
        parent: Basic.Overlay.overlay
        property string contextSeriesUid: ""
        property real requestedSceneX: 0
        property real requestedSceneY: 0
        width: Math.min(360, parent.width - 16)
        height: menuContent.implicitHeight + topPadding + bottomPadding
        padding: 7
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
            } else if (["2d", "mpr", "tag", "3d"].includes(action)) {
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
            color: Theme.panelBackgroundStrong
            border.color: Theme.borderDefault
            border.width: 1
            radius: 8
        }

        contentItem: Column {
            id: menuContent
            spacing: 2

            Repeater {
                model: leftPanel.contextActions
                delegate: Item {
                    id: menuAction
                    required property var modelData
                    readonly property bool actionEnabled: modelData.supported
                        && (leftPanel.panelController.seriesModality(
                                seriesContextMenu.contextSeriesUid) !== "PT"
                            || modelData.code === "2d"
                            || modelData.code === "tag"
                            || modelData.code === "mpr"
                            || modelData.code === "fusion"
                            || modelData.code === "directory"
                            || modelData.code === "remove")
                    objectName: "seriesContextAction-" + modelData.code
                    width: menuContent.width
                    height: modelData.separatorBefore ? 58 : 52

                    Rectangle {
                        visible: menuAction.modelData.separatorBefore
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.right: parent.right
                        height: 1
                        color: Theme.borderSubtle
                    }

                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 52
                        radius: 6
                        color: menuAction.actionEnabled && menuHover.hovered
                            ? Theme.cardBackgroundHover : Theme.cardBackground
                        border.color: menuAction.modelData.danger
                            ? Theme.dangerSurface : Theme.borderSubtle
                        opacity: menuAction.actionEnabled ? 1 : 0.45

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            spacing: 10

                            Rectangle {
                                Layout.preferredWidth: menuAction.modelData.badge.length > 3 ? 54 : 46
                                Layout.preferredHeight: 26
                                radius: 13
                                color: menuAction.modelData.danger ? Theme.dangerSurface : Theme.secondarySoft
                                border.color: menuAction.modelData.danger ? Theme.dangerColor : Theme.borderStrong
                                Text {
                                    anchors.centerIn: parent
                                    text: menuAction.modelData.badge
                                    color: menuAction.modelData.danger ? Theme.dangerColor : Theme.textPrimary
                                    font.pixelSize: menuAction.modelData.badge.length > 3 ? 9 : 10
                                    font.weight: Font.DemiBold
                                    font.letterSpacing: 1.2
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1
                                Text {
                                    Layout.fillWidth: true
                                    text: menuAction.modelData.label
                                    color: menuAction.modelData.danger ? Theme.dangerColor : Theme.textPrimary
                                    font.pixelSize: 13
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideRight
                                }
                                Text {
                                    Layout.fillWidth: true
                                    visible: text !== ""
                                    text: menuAction.modelData.description
                                    color: Theme.textMuted
                                    font.pixelSize: 10
                                    elide: Text.ElideRight
                                }
                            }
                        }
                    }

                    HoverHandler {
                        id: menuHover
                        cursorShape: menuAction.actionEnabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                    }
                    TapHandler {
                        enabled: menuAction.actionEnabled
                        onTapped: seriesContextMenu.triggerAction(menuAction.modelData.code)
                    }
                    Basic.ToolTip.visible: menuHover.hovered && !menuAction.actionEnabled
                    Basic.ToolTip.delay: 350
                    Basic.ToolTip.text: leftPanel.panelController.seriesModality(
                        seriesContextMenu.contextSeriesUid) === "PT"
                        ? "暂不支持 PET 体绘制或动态浏览"
                        : "暂未实现"
                }
            }
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
