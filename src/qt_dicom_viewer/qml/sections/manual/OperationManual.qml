pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"
import "../center/viewportArea" as ViewportUi

Rectangle {
    id: manual
    objectName: "operationManual"
    required property var controller
    readonly property var article: controller?.currentChapter ?? ({})
    readonly property string chapter: controller?.chapterId ?? ""
    property bool restoring: true
    property bool active: true
    onActiveChanged: {
        if (active) restorePosition()
        else restoring = true
    }
    property bool petExample: false
    color: Theme.panelBackgroundStrong

    function revealChapter(button) {
        Qt.callLater(function() {
            if (!button.checked) return
            const scroller = navigationScroll.contentItem
            const top = button.mapToItem(scroller.contentItem, 0, 0).y
            const bottom = top + button.height
            if (top < scroller.contentY)
                scroller.contentY = top
            else if (bottom > scroller.contentY + scroller.height)
                scroller.contentY = bottom - scroller.height
        })
    }

    function restorePosition() {
        restoring = true
        restoreTimer.restart()
    }
    Timer {
        id: restoreTimer
        // Incubation completes before wrapped text and images finish layout.
        // Restore only after their geometry has settled, without saving the
        // temporary zero/clamped offset back into the chapter controller.
        interval: 16
        onTriggered: {
            if (!manual.controller || !manual.active) return
            readingArea.contentY = Math.max(0, Math.min(manual.controller.scrollPosition,
                readingArea.contentHeight - readingArea.height))
            manual.restoring = false
        }
    }
    Component.onCompleted: restorePosition()
    Connections {
        target: manual.controller
        function onChapterChanged() { manual.restorePosition() }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0
        Rectangle {
            id: navigation
            objectName: "manualNavigation"
            Layout.preferredWidth: manual.width < 760 ? 154 : 190
            Layout.fillHeight: true
            color: Theme.panelBackground
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 10
                RowLayout {
                    Components.AppIcon { iconName: "manual"; iconSize: 18; iconColor: Theme.primaryColor }
                    Text { text: "操作手册"; color: Theme.textPrimary; font.pixelSize: 16; font.weight: Font.DemiBold }
                }
                Components.AppTextField {
                    id: search
                    objectName: "manualSearch"
                    Layout.fillWidth: true
                    placeholderText: "搜索章节或操作"
                    text: manual.controller?.search ?? ""
                    onTextEdited: manual.controller?.setSearch(text)
                }
                Basic.ScrollView {
                    id: navigationScroll
                    objectName: "manualNavigationScroll"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentWidth: availableWidth
                    rightPadding: 10
                    clip: true
                    Basic.ScrollBar.vertical: Components.AppScrollBar {}
                    Basic.ScrollBar.horizontal.policy: Basic.ScrollBar.AlwaysOff
                    ColumnLayout {
                        width: navigationScroll.availableWidth
                        spacing: 4
                        Repeater {
                            model: manual.controller?.navigation ?? []
                            delegate: ColumnLayout {
                                id: categoryEntry
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.minimumWidth: 0
                                spacing: 3
                                Text {
                                    objectName: "manualCategory-" + categoryEntry.modelData.id
                                    Layout.fillWidth: true
                                    Layout.topMargin: 10
                                    Layout.bottomMargin: 4
                                    text: categoryEntry.modelData.title
                                    color: Theme.textMuted
                                    font.pixelSize: 11
                                    wrapMode: Text.Wrap
                                }
                                Repeater {
                                    model: categoryEntry.modelData.chapters
                                    delegate: Components.AppButton {
                                        id: chapterButton
                                        required property var modelData
                                        objectName: "manualChapter-" + modelData.id
                                        Layout.fillWidth: true
                                        implicitHeight: Math.max(32, chapterTitle.implicitHeight + 12)
                                        minimumButtonWidth: 0
                                        leftPadding: 8
                                        rightPadding: 8
                                        momentary: true
                                        normalColor: "transparent"
                                        activeBorderColor: "transparent"
                                        checked: manual.chapter === modelData.id
                                        onCheckedChanged: if (checked) manual.revealChapter(chapterButton)
                                        Component.onCompleted: if (checked) manual.revealChapter(chapterButton)
                                        Accessible.name: categoryEntry.modelData.title + " · " + modelData.title
                                        onClicked: manual.controller.selectChapter(modelData.id)
                                        contentItem: Text {
                                            id: chapterTitle
                                            text: chapterButton.modelData.title
                                            color: chapterButton.checked ? Theme.primaryColor : Theme.textSecondary
                                            font.pixelSize: 12
                                            wrapMode: Text.Wrap
                                            verticalAlignment: Text.AlignVCenter
                                        }
                                    }
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: (manual.controller?.navigation.length ?? 0) === 0
                            text: "没有匹配章节\n请尝试其他关键词"
                            color: Theme.textMuted
                            font.pixelSize: 12
                            wrapMode: Text.Wrap
                        }
                    }
                }
            }
        }
        Flickable {
            id: readingArea
            objectName: "manualReadingArea"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: 0
            contentWidth: width
            contentHeight: readingContent.implicitHeight + 40
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            onMovementStarted: { restoreTimer.stop(); manual.restoring = false }
            onContentHeightChanged: if (manual.active && manual.restoring) restoreTimer.restart()
            onHeightChanged: if (manual.active && manual.restoring) restoreTimer.restart()
            onContentYChanged: if (manual.active && !manual.restoring) manual.controller?.setScrollPosition(contentY)
            Basic.ScrollBar.vertical: Components.AppScrollBar {}
            ColumnLayout {
                id: readingContent
                x: 20; y: 20
                width: Math.max(1, readingArea.width - 48)
                spacing: 16
                Text {
                    Layout.fillWidth: true
                    text: "操作手册  /  " + (manual.article.categoryTitle ?? "")
                    color: Theme.textMuted
                    font.pixelSize: 11
                    wrapMode: Text.Wrap
                }
                Text {
                    objectName: "manualChapterTitle"
                    Layout.fillWidth: true
                    text: manual.article.title ?? ""
                    color: Theme.textPrimary
                    font.pixelSize: 22
                    font.weight: Font.DemiBold
                    wrapMode: Text.Wrap
                }
                VoiManualFigure {
                    Layout.fillWidth: true
                    Layout.preferredHeight: visible ? width * 220 / 760 : 0
                    visible: !!manual.article.figure
                    chapter: manual.article.figure ?? ""
                }
                Repeater {
                    model: manual.article.sections ?? []
                    delegate: ColumnLayout {
                        id: step
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 7
                        Text {
                            Layout.fillWidth: true
                            text: step.modelData.title
                            textFormat: Text.PlainText
                            color: Theme.textPrimary
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                            wrapMode: Text.Wrap
                        }
                        Text {
                            Layout.fillWidth: true
                            text: step.modelData.body
                            textFormat: Text.PlainText
                            color: Theme.textSecondary
                            font.pixelSize: 13
                            lineHeight: 1.5
                            wrapMode: Text.Wrap
                        }
                    }
                }
                GridLayout {
                    Layout.fillWidth: true
                    visible: manual.article.cursorLegend ?? false
                    columns: width < 600 ? 2 : 3
                    columnSpacing: 8; rowSpacing: 8
                    Repeater {
                        model: [{key:"segmentation",label:"箭头 + 分割"}, {key:"voi",label:"箭头 + VOI"},
                            {key:"pan",label:"移动 / 平移"}, {key:"resize",label:"调整尺寸"},
                            {key:"crosshair-move",label:"十字线定位"}, {key:"crosshair-rotate",label:"旋转切面"},
                            {key:"window",label:"调窗"}, {key:"zoom",label:"缩放"}, {key:"scroll",label:"翻页"}]
                        delegate: Rectangle {
                            id: legend
                            required property var modelData
                            Layout.fillWidth: true
                            implicitHeight: 50
                            color: Theme.panelBackground
                            radius: 4
                            RowLayout {
                                anchors.fill: parent; anchors.margins: 8
                                ViewportUi.CursorGlyph {
                                    visible: true
                                    Layout.preferredWidth: 40; Layout.preferredHeight: 32; iconName: legend.modelData.key
                                }
                                Text { Layout.fillWidth: true; text: legend.modelData.label; color: Theme.textSecondary; font.pixelSize: 12; wrapMode: Text.Wrap }
                            }
                        }
                    }
                }
                RowLayout {
                    visible: (manual.article.examples?.length ?? 0) > 0
                    Text { text: "合成数据示例"; color: Theme.textMuted; font.pixelSize: 12 }
                    Components.AppButton { text: "CT"; compact: true; checked: !manual.petExample; onClicked: manual.petExample = false }
                    Components.AppButton { text: "PET"; compact: true; checked: manual.petExample; onClicked: manual.petExample = true }
                }
                Image {
                    id: example
                    objectName: "manualExample"
                    readonly property string file: manual.article.example
                        ?? ((manual.article.examples?.length ?? 0) > 0 ? manual.article.examples[manual.petExample ? 1 : 0] : "")
                    Layout.fillWidth: true
                    Layout.preferredHeight: visible && sourceSize.width > 0 ? width * sourceSize.height / sourceSize.width : 0
                    visible: file !== ""
                    fillMode: Image.PreserveAspectFit
                    source: file ? "../../assets/help/" + file : ""
                    smooth: true
                }
            }
        }
    }
}
