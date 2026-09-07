pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Window
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"
import "../center/viewportArea" as ViewportUi

Window {
    id: manual
    objectName: "operationManual"
    required property var ownerWindow
    // A normal application window can be placed beside the images or on
    // another screen; it is neither modal nor kept above the image window.
    transientParent: null
    flags: Qt.Window
    modality: Qt.NonModal
    title: "操作手册 · Qt DICOM Viewer"
    color: Theme.panelBackgroundStrong
    visible: false
    property string chapter: "segmentation"
    property bool petExample: false
    readonly property string category: "mpr-segmentation"
    readonly property var categories: [
        { key: "mpr-segmentation", title: "MPR 分割", initialChapter: "segmentation" }
    ]
    readonly property var chapters: [
        { key: "segmentation", title: "阈值分割与深度" },
        { key: "voi", title: "VOI 分析" },
        { key: "quantification", title: "CT / PET 定量" },
        { key: "interaction", title: "鼠标交互" },
        { key: "management", title: "范围管理" }
    ]
    readonly property var articles: ({
        segmentation: [
            { title: "1. 框选需要分割的范围", body: "在 CT 或 PET 的 MPR 页面选择「阈值分割」，勾选「启用」。在轴位、冠状位或矢状位按住鼠标左键拖出矩形，松开完成。分割范围会同时显示在三个切面中。" },
            { title: "2. 设置阈值，查看着色结果", body: "在右侧选择「绝对值」或「%」，在下一行输入阈值，也可拖动滑块。范围内数值大于或等于阈值的部分会着色，并更新统计。CT 使用 HU；PET 先确认定量单位。" },
            { title: "3. 确认分割深度", body: "深度以绘制切面为中心向两侧延伸。默认按 √(宽 × 高) 自动计算，例如 32 × 18 mm 对应深度 24 mm，最小为一个切面采样间距。拖动角点改变宽高时，自动深度一起变化。" },
            { title: "4. 调整范围或手动深度", body: "在原绘制切面拖动矩形内部可移动范围，拖动角点可调整宽高。直接输入或拖动深度滑块会切换到「手动」，以后调整宽高保留这一深度；点击「手动」切回「自动」即可恢复跟随。拖动时预览轮廓，松开后更新统计和着色。" },
            { title: "没有看到分割结果？", body: "先检查范围是否覆盖目标、深度是否足够，以及阈值和单位是否合适。N 为 0 表示没有符合条件的有效体素。PET 的 MIP 是投影视图，请在其他三个切面操作。启用分割会关闭厚层投影和手动配准。" }
        ],
        voi: [
            { title: "1. 从圆心向外绘制", body: "选择「VOI」并勾选「启用」。在一个 MPR 切面按下左键确定圆心，向外拖动确定半径，松开完成。水平或垂直拖动都可以绘制，范围按实际毫米尺寸计算。" },
            { title: "2. 调整位置与大小", body: "回到原绘制切面，拖动圆内可移动范围；拖动圆周或四个控制点可调整半径。也可在右侧直接输入直径。VOI 统计范围内全部有效体素，不使用分割阈值。" },
            { title: "3. 在球体与椭球之间调整", body: "自动模式下深度等于直径，形成球体。手动改变深度后形成椭球：绘制切面仍是圆形，侧面可能是椭圆。切回「自动」可恢复球体。" },
            { title: "翻页后圆变小或消失？", body: "这是该三维范围与当前切面的实际交集。越远离中心，截面越小；切面超出范围后轮廓消失。可翻回原切面继续编辑。PET MIP 不支持 VOI 绘制，请使用轴位、冠状位或矢状位。" }
        ],
        quantification: [
            { title: "先确认单位", body: "CT 使用 HU。PET 根据数据提供 SUVbw、原生 SUV 或 Bq/ml、kBq/ml 等单位；没有 SUV 选项时，使用当前可用单位设置阈值。PET/CT 融合中，在 CT 格绘制使用 CT 定量，在 PET 或融合格绘制使用 PET 定量。" },
            { title: "绝对值与百分比", body: "绝对值直接使用当前单位，例如 HU ≥ 300。PET 百分比以范围内最大值为基准；CT 百分比在范围内最小值与最大值之间取值，例如最小 −100、最大 300 时，50% 对应 100 HU。" },
            { title: "切换 PET 单位后重新检查阈值", body: "每个范围的定量单位单独保存，调窗或切换影像显示单位不会改变它。切换范围的定量单位后，绝对阈值会重置为 SUV 2.5 或源单位 0，请重新设置；百分比数值保留，并在新单位下重新计算。" },
            { title: "如何阅读统计", body: "MEAN、MIN、MAX 分别为均值、最小值、最大值；SD 为标准差；N 为体素数；VOL 为体积，单位 cm³。分割只统计符合阈值的部分，VOI 统计整个范围；保留率表示分割后留下的有效体素比例。" },
            { title: "统计与显示的关系", body: "统计来自原始三维影像数据，不随窗宽窗位或屏幕亮度变化。无有效结果时，N 与 VOL 为 0，其余统计为 --。改变深度或边界时，体素数和体积可能逐级变化。" }
        ],
        interaction: [
            { title: "新建、移动与调整尺寸", body: "启用分割或 VOI 后，先在列表选择要编辑的范围。在原绘制切面，范围内部显示移动箭头；矩形角点或 VOI 圆周显示尺寸调整箭头。在范围外按住左键拖动可新建。光标在一次拖动中保持当前操作，松开后更新结果。" },
            { title: "翻页与十字线", body: "滚轮用于翻页，翻回原绘制切面可继续编辑范围。启用分割或 VOI 时，即使鼠标经过十字线，也优先绘制或编辑范围。若要移动十字线或旋转切面，请切换到调窗等其他工具：拖动中心移动定位，拖动线段旋转切面。" },
            { title: "切换到其他影像操作", body: "调窗显示半明半暗圆，缩放显示放大镜，翻页显示上下箭头，图像平移显示四向箭头。测量绘制使用十字光标，选中测量对象后可用移动箭头拖动。十字线切面旋转与整体三维旋转使用不同图标。" },
            { title: "取消与删除", body: "在影像窗口按 Esc 取消本次绘制或编辑，恢复原范围；按 Delete 或 Backspace 删除选中范围。编辑输入框时，先点击影像使其获得焦点。手册窗口中的 Esc 或关闭快捷键只关闭手册，不删除范围。" }
        ],
        management: [
            { title: "选择、命名与显示", body: "点击列表名称选中范围并进入对应工具，双击名称可改名。点击左侧圆点显示或隐藏这一项，点击 × 删除。关闭「启用」会隐藏全部范围并暂停绘制，重新启用可继续使用已有结果。" },
            { title: "清除的作用范围", body: "底部「清除分割」或「清除 VOI」删除当前类型的范围；「全部清除」删除当前 MPR 标签页的全部分割和 VOI，不影响其他标签页。没有可清除内容时按钮禁用。" },
            { title: "关闭手册与关闭影像标签页", body: "关闭手册窗口不会改变影像、范围或参数。范围保留在当前影像标签页中，关闭该标签页后清除。目前不提供分割文件导入导出。手册中的示例使用合成数据。" }
        ]
    })
    width: Math.min(1060, Screen.desktopAvailableWidth - 32)
    height: Math.min(800, Screen.desktopAvailableHeight - 48)
    minimumWidth: 720
    minimumHeight: 560
    function showChapter(value) {
        chapter = chapters.some(entry => entry.key === value) ? value : "segmentation"
        readingArea.contentY = 0
        if (visibility === Window.Minimized) showNormal()
        else show()
        raise()
        requestActivate()
    }
    onChapterChanged: if (readingArea) readingArea.contentY = 0
    Connections {
        target: manual.ownerWindow
        function onClosing(close) { manual.close() }
    }
    Shortcut { sequence: "Esc"; onActivated: manual.close() }
    Shortcut { sequences: [StandardKey.Close]; onActivated: manual.close() }
    ColumnLayout {
        anchors.fill: parent
        clip: true
        spacing: 0
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: 16
            Text {
                Layout.fillWidth: true
                text: "操作手册"
                color: Theme.textPrimary
                font.pixelSize: 20
                font.weight: Font.DemiBold
            }
            Components.AppButton {
                objectName: "voiManualClose"
                compact: true
                text: "关闭"
                onClicked: manual.close()
            }
        }
        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.dividerColor }
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0
            Rectangle {
                objectName: "manualNavigation"
                Layout.preferredWidth: manual.width < 760 ? 148 : 188
                Layout.fillHeight: true
                color: Theme.panelBackground
                Basic.ScrollView {
                    anchors.fill: parent
                    anchors.margins: 10
                    contentWidth: availableWidth
                    clip: true
                    ColumnLayout {
                        width: parent.width
                        spacing: 6
                        Text {
                            Layout.topMargin: 8
                            Layout.bottomMargin: 8
                            text: "影像操作"
                            color: Theme.textMuted
                            font.pixelSize: 11
                        }
                        Repeater {
                            model: manual.categories
                            delegate: ColumnLayout {
                                id: categoryEntry
                                required property var modelData
                                Layout.fillWidth: true
                                spacing: 3
                                Components.AppButton {
                                    id: categoryButton
                                    objectName: "manualCategory-" + categoryEntry.modelData.key
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 40
                                    checked: manual.category === categoryEntry.modelData.key
                                    onClicked: manual.chapter = categoryEntry.modelData.initialChapter
                                    Accessible.name: categoryEntry.modelData.title
                                    contentItem: Text {
                                        text: categoryEntry.modelData.title
                                        color: categoryButton.checked ? Theme.textPrimary : Theme.textSecondary
                                        font.pixelSize: 14
                                        font.weight: Font.DemiBold
                                        verticalAlignment: Text.AlignVCenter
                                        elide: Text.ElideRight
                                    }
                                }
                                Repeater {
                                    model: categoryEntry.modelData.key === "mpr-segmentation"
                                        ? manual.chapters : []
                                    delegate: Components.AppButton {
                                        id: chapterButton
                                        required property var modelData
                                        objectName: "voiManualChapter-" + modelData.key
                                        Layout.fillWidth: true
                                        Layout.leftMargin: 12
                                        Layout.minimumWidth: 0
                                        Layout.preferredHeight: 34
                                        visible: manual.category === categoryEntry.modelData.key
                                        checked: manual.chapter === modelData.key
                                        onClicked: manual.chapter = modelData.key
                                        Accessible.name: "MPR 分割 · " + modelData.title
                                        contentItem: Text {
                                            text: chapterButton.modelData.title
                                            color: chapterButton.checked ? Theme.textPrimary : Theme.textSecondary
                                            font.pixelSize: 12
                                            elide: Text.ElideRight
                                            verticalAlignment: Text.AlignVCenter
                                        }
                                        background: Rectangle {
                                            radius: 4
                                            color: chapterButton.checked ? Theme.selectionBackground : chapterButton.hovered ? Theme.controlHover : "transparent"
                                            Rectangle {
                                                width: 3; height: 18; radius: 1
                                                anchors.left: parent.left
                                                anchors.verticalCenter: parent.verticalCenter
                                                color: Theme.primaryColor
                                                visible: chapterButton.checked
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: Theme.dividerColor }
            Flickable {
                id: readingArea
                objectName: "voiManualReadingArea"
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: readingContent.implicitHeight + 40
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                Basic.ScrollBar.vertical: Components.AppScrollBar {}
                ColumnLayout {
                    id: readingContent
                    x: 20; y: 20
                    width: Math.max(1, readingArea.width - 48)
                    spacing: 16
                    Text {
                        objectName: "manualBreadcrumb"
                        Layout.fillWidth: true
                        visible: manual.category === "mpr-segmentation"
                        text: "操作手册  /  MPR 分割"
                        color: Theme.textMuted
                        font.pixelSize: 11
                        wrapMode: Text.Wrap
                    }
                    Text {
                        objectName: "manualChapterTitle"
                        Layout.fillWidth: true
                        text: manual.chapters.find(entry => entry.key === manual.chapter)?.title ?? ""
                        color: Theme.textPrimary
                        font.pixelSize: 22
                        font.weight: Font.DemiBold
                        wrapMode: Text.Wrap
                    }
                    VoiManualFigure {
                        Layout.fillWidth: true
                        Layout.preferredHeight: width * 220 / 760
                        visible: manual.chapter !== "interaction"
                        chapter: manual.chapter
                    }
                    Repeater {
                        model: manual.articles[manual.chapter] ?? []
                        delegate: ColumnLayout {
                            id: articleStep
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            spacing: 6
                            Text {
                                Layout.fillWidth: true
                                text: articleStep.modelData.title
                                wrapMode: Text.Wrap
                                color: Theme.textPrimary
                                font.pixelSize: 15
                                font.weight: Font.DemiBold
                            }
                            Text {
                                Layout.fillWidth: true
                                Layout.minimumWidth: 0
                                text: articleStep.modelData.body
                                wrapMode: Text.Wrap
                                lineHeight: 1.4
                                color: Theme.textSecondary
                                font.pixelSize: 14
                            }
                        }
                    }
                    GridLayout {
                        objectName: "manualCursorLegend"
                        Layout.fillWidth: true
                        visible: manual.chapter === "interaction"
                        columns: width < 600 ? 2 : 3
                        columnSpacing: 8
                        rowSpacing: 8
                        Repeater {
                            model: [
                                { key: "segmentation", label: "新建分割" },
                                { key: "voi", label: "新建 VOI" },
                                { key: "pan", label: "移动范围 / 平移" },
                                { key: "resize", label: "调整范围尺寸" },
                                { key: "crosshair-move", label: "十字线定位" },
                                { key: "crosshair-rotate", label: "旋转切面" },
                                { key: "window", label: "调窗" },
                                { key: "zoom", label: "缩放" },
                                { key: "scroll", label: "翻页" }
                            ]
                            delegate: Rectangle {
                                id: legendEntry
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.minimumWidth: 0
                                implicitHeight: 52
                                radius: 4
                                color: Theme.panelBackground
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    spacing: 10
                                    ViewportUi.CursorGlyph {
                                        Layout.preferredWidth: 24
                                        Layout.preferredHeight: 24
                                        iconName: legendEntry.modelData.key
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: legendEntry.modelData.label
                                        color: Theme.textSecondary
                                        font.pixelSize: 12
                                        wrapMode: Text.Wrap
                                    }
                                }
                            }
                        }
                    }
                    RowLayout {
                        visible: ["segmentation", "quantification", "voi"].includes(manual.chapter)
                        Text { text: "合成数据示例"; color: Theme.textMuted; font.pixelSize: 12 }
                        Components.AppButton {
                            compact: true; text: "CT"; checked: !manual.petExample
                            onClicked: manual.petExample = false
                        }
                        Components.AppButton {
                            compact: true; text: "PET"; checked: manual.petExample
                            onClicked: manual.petExample = true
                        }
                    }
                    Image {
                        objectName: "voiManualExample"
                        Layout.fillWidth: true
                        Layout.preferredHeight: visible ? width * 1120 / 1550 : 0
                        visible: ["segmentation", "quantification", "voi"].includes(manual.chapter)
                        fillMode: Image.PreserveAspectFit
                        source: "../../assets/help/" + (manual.chapter === "voi" ? "voi-" : "segmentation-")
                            + (manual.petExample ? "pt" : "ct") + ".png"
                    }
                }
            }
        }
    }
}
