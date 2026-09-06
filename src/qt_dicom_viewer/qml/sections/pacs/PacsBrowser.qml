pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"

Rectangle {
    id: browser
    objectName: "pacsBrowser"
    required property var pacsController
    required property var workspaceController
    readonly property bool available: pacsController.pacsEnabled && pacsController.enabledProfiles.length > 0
    color: Theme.panelBackgroundStrong

    component Caption: Text {
        color: Theme.textMuted
        font.pixelSize: 11
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15
        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                Text {
                    Layout.fillWidth: true
                    text: "PACS 浏览器"
                    color: Theme.textPrimary
                    font.pixelSize: 23
                    font.bold: true
                }
                Text {
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                    text: "查询检查，选择序列并导入工作区"
                    color: Theme.textMuted
                    font.pixelSize: 12
                }
            }
            Components.AppButton {
                objectName: "pacsManageSources"
                text: "管理数据源"
                onClicked: browser.workspaceController.openSettings()
            }
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: Theme.dividerColor
        }
        RowLayout {
            visible: browser.available
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 15
            ColumnLayout {
                Layout.preferredWidth: browser.width < 900 ? 190 : 225
                Layout.maximumWidth: browser.width < 900 ? 190 : 225
                Layout.fillHeight: true
                spacing: 10
                Basic.ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentWidth: availableWidth
                    clip: true
                    ColumnLayout {
                        width: parent.width
                        spacing: 8
                        Caption {
                            text: "连接配置"
                        }
                        Components.AppComboBox {
                            id: profileChoice
                            objectName: "pacsProfileChoice"
                            Layout.fillWidth: true
                            model: browser.pacsController.enabledProfiles
                            textRole: "name"
                            currentIndex: {
                                const rows = browser.pacsController.enabledProfiles;
                                for (let i = 0; i < rows.length; i++)
                                    if (rows[i].id === browser.pacsController.selectedProfileId)
                                        return i;
                                return -1;
                            }
                            enabled: !browser.pacsController.busy
                            onActivated: index => browser.pacsController.selectProfile(browser.pacsController.enabledProfiles[index].id)
                        }
                        Caption {
                            text: "患者姓名"
                            Layout.topMargin: 5
                        }
                        Components.AppTextField {
                            id: patientName
                            objectName: "pacsPatientName"
                            Layout.fillWidth: true
                            placeholderText: "Patient*"
                            text: browser.pacsController.filterInputs.PatientName || ""
                            enabled: !browser.pacsController.busy
                        }
                        Caption {
                            text: "患者 ID"
                        }
                        Components.AppTextField {
                            id: patientId
                            objectName: "pacsPatientId"
                            Layout.fillWidth: true
                            placeholderText: "ID…"
                            text: browser.pacsController.filterInputs.PatientID || ""
                            enabled: !browser.pacsController.busy
                        }
                        Caption {
                            text: "检查号"
                        }
                        Components.AppTextField {
                            id: accession
                            objectName: "pacsAccession"
                            Layout.fillWidth: true
                            placeholderText: "Accession…"
                            text: browser.pacsController.filterInputs.AccessionNumber || ""
                            enabled: !browser.pacsController.busy
                        }
                        Caption {
                            text: "模态"
                        }
                        Components.AppComboBox {
                            id: modality
                            Layout.fillWidth: true
                            model: ["全部", "CT", "MR", "PT", "CR", "DX", "US", "MG", "NM", "XA", "RF", "OT"]
                            currentIndex: Math.max(0, model.indexOf(browser.pacsController.filterInputs.ModalitiesInStudy || "全部"))
                            enabled: !browser.pacsController.busy
                        }
                        Caption {
                            text: "开始日期（可留空）"
                        }
                        Components.AppTextField {
                            id: dateFrom
                            objectName: "pacsDateFrom"
                            Layout.fillWidth: true
                            placeholderText: "YYYY-MM-DD"
                            text: browser.pacsController.filterInputs.dateFrom || ""
                            enabled: !browser.pacsController.busy
                        }
                        Caption {
                            text: "结束日期（可留空）"
                        }
                        Components.AppTextField {
                            id: dateTo
                            objectName: "pacsDateTo"
                            Layout.fillWidth: true
                            placeholderText: "YYYY-MM-DD"
                            text: browser.pacsController.filterInputs.dateTo || ""
                            enabled: !browser.pacsController.busy
                        }
                        Caption {
                            text: "每页数量"
                        }
                        Components.AppComboBox {
                            id: pageSize
                            Layout.fillWidth: true
                            model: ["20", "50", "100"]
                            currentIndex: model.indexOf(String(browser.pacsController.pageSize))
                            enabled: !browser.pacsController.busy
                        }
                        Components.AppButton {
                            Layout.fillWidth: true
                            text: advanced.visible ? "收起更多条件  ⌃" : "更多筛选条件  ⌄"
                            onClicked: advanced.visible = !advanced.visible
                        }
                        ColumnLayout {
                            id: advanced
                            Layout.fillWidth: true
                            visible: false
                            spacing: 8
                            Caption {
                                text: "检查 UID"
                            }
                            Components.AppTextField {
                                id: studyUid
                                Layout.fillWidth: true
                                text: browser.pacsController.filterInputs.StudyInstanceUID || ""
                                enabled: !browser.pacsController.busy
                            }
                            Caption {
                                text: "检查描述"
                            }
                            Components.AppTextField {
                                id: description
                                Layout.fillWidth: true
                                text: browser.pacsController.filterInputs.StudyDescription || ""
                                enabled: !browser.pacsController.busy
                            }
                        }
                    }
                }
                Components.AppButton {
                    objectName: "pacsQueryStudies"
                    Layout.fillWidth: true
                    text: browser.pacsController.busy && browser.pacsController.operation === "studies" ? "查询中…" : "查询检查"
                    normalColor: Theme.primaryButtonBackground
                    enabled: !browser.pacsController.busy
                    onClicked: browser.pacsController.queryStudies({
                        PatientName: patientName.text,
                        PatientID: patientId.text,
                        AccessionNumber: accession.text,
                        ModalitiesInStudy: modality.currentIndex > 0 ? modality.currentText : "",
                        dateFrom: dateFrom.text,
                        dateTo: dateTo.text,
                        StudyInstanceUID: studyUid.text,
                        StudyDescription: description.text
                    }, Number(pageSize.currentText))
                }
            }
            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color: Theme.dividerColor
            }
            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                spacing: 10
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: "检查"
                        color: Theme.textPrimary
                        font.pixelSize: 15
                        font.bold: true
                    }
                    Components.AppButton {
                        objectName: "pacsStudyPrevious"
                        text: "‹"
                        compact: true
                        minimumButtonWidth: 26
                        enabled: !browser.pacsController.busy && browser.pacsController.studyPage > 1
                        onClicked: browser.pacsController.changeStudyPage(-1)
                    }
                    Caption {
                        text: browser.pacsController.studyPage
                    }
                    Components.AppButton {
                        objectName: "pacsStudyNext"
                        text: "›"
                        compact: true
                        minimumButtonWidth: 26
                        enabled: !browser.pacsController.busy && browser.pacsController.hasStudyNext
                        onClicked: browser.pacsController.changeStudyPage(1)
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: Theme.cardBackground
                    border.color: Theme.borderDefault
                    radius: 10
                    ListView {
                        id: studiesList
                        objectName: "pacsStudiesList"
                        anchors.fill: parent
                        anchors.margins: 7
                        clip: true
                        spacing: 6
                        model: browser.pacsController.studies
                        Basic.ScrollBar.vertical: Basic.ScrollBar {}
                        delegate: Rectangle {
                            id: studyRow
                            required property var modelData
                            objectName: "pacsStudy-" + modelData.uid
                            width: studiesList.width
                            height: studyContent.implicitHeight + 24
                            radius: 7
                            color: browser.pacsController.selectedStudyUid === modelData.uid ? Theme.selectionBackground : studyHover.hovered ? Theme.cardBackgroundHover : Theme.panelBackgroundStrong
                            border.color: browser.pacsController.selectedStudyUid === modelData.uid ? Theme.selectionBorder : Theme.borderSubtle
                            ColumnLayout {
                                id: studyContent
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 6
                                Text {
                                    Layout.fillWidth: true
                                    text: studyRow.modelData.patientName || "未知患者"
                                    color: Theme.textPrimary
                                    font.pixelSize: 14
                                    font.bold: true
                                    elide: Text.ElideRight
                                }
                                Caption {
                                    Layout.fillWidth: true
                                    text: "ID  " + (studyRow.modelData.patientId || "—")
                                    elide: Text.ElideRight
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: studyRow.modelData.description || "未命名检查"
                                    color: Theme.textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.Wrap
                                }
                                Caption {
                                    Layout.fillWidth: true
                                    text: (studyRow.modelData.date || "日期未知") + "  ·  " + (studyRow.modelData.modality || "—")
                                    wrapMode: Text.Wrap
                                }
                                Caption {
                                    Layout.fillWidth: true
                                    text: "检查号  " + (studyRow.modelData.accession || "—")
                                    elide: Text.ElideRight
                                }
                            }
                            HoverHandler {
                                id: studyHover
                                cursorShape: Qt.PointingHandCursor
                            }
                            TapHandler {
                                enabled: !browser.pacsController.busy
                                onTapped: browser.pacsController.selectStudy(studyRow.modelData.uid)
                            }
                        }
                    }
                    Text {
                        anchors.centerIn: parent
                        width: parent.width - 28
                        visible: browser.pacsController.studies.length === 0
                        text: browser.pacsController.busy && browser.pacsController.operation === "studies" ? "正在查询…" : "设置查询条件后\n点击“查询检查”。"
                        color: Theme.textSubtle
                        wrapMode: Text.Wrap
                        horizontalAlignment: Text.AlignHCenter
                        font.pixelSize: 12
                        lineHeight: 1.6
                    }
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                spacing: 10
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: "序列"
                        color: Theme.textPrimary
                        font.pixelSize: 15
                        font.bold: true
                    }
                    Components.AppButton {
                        objectName: "pacsSeriesPrevious"
                        text: "‹"
                        compact: true
                        minimumButtonWidth: 26
                        enabled: !browser.pacsController.busy && browser.pacsController.seriesPage > 1
                        onClicked: browser.pacsController.changeSeriesPage(-1)
                    }
                    Caption {
                        text: browser.pacsController.seriesPage
                    }
                    Components.AppButton {
                        objectName: "pacsSeriesNext"
                        text: "›"
                        compact: true
                        minimumButtonWidth: 26
                        enabled: !browser.pacsController.busy && browser.pacsController.hasSeriesNext
                        onClicked: browser.pacsController.changeSeriesPage(1)
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: Theme.cardBackground
                    border.color: Theme.borderDefault
                    radius: 10
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 7
                        spacing: 6
                        Components.AppCheckBox {
                            objectName: "pacsSelectAll"
                            text: "全选本页"
                            enabled: browser.pacsController.series.length > 0 && !browser.pacsController.busy
                            checked: browser.pacsController.selectedCount > 0 && browser.pacsController.selectedCount === browser.pacsController.series.length
                            onClicked: browser.pacsController.selectAllSeries(checked)
                        }
                        ListView {
                            id: seriesList
                            objectName: "pacsSeriesList"
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            spacing: 6
                            model: browser.pacsController.series
                            Basic.ScrollBar.vertical: Basic.ScrollBar {}
                            delegate: Rectangle {
                                id: seriesRow
                                readonly property bool selected: browser.pacsController.selectedSeriesUids.indexOf(modelData.uid) >= 0
                                required property var modelData
                                width: seriesList.width
                                height: seriesContent.implicitHeight + 24
                                radius: 7
                                color: seriesRow.selected ? Theme.selectionBackground : Theme.panelBackgroundStrong
                                border.color: seriesRow.selected ? Theme.selectionBorder : Theme.borderSubtle
                                ColumnLayout {
                                    id: seriesContent
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 6
                                    Components.AppCheckBox {
                                        objectName: "pacsSeries-" + seriesRow.modelData.uid
                                        text: (seriesRow.modelData.modality || "DICOM") + "  " + (seriesRow.modelData.number || "")
                                        checked: seriesRow.selected
                                        enabled: !browser.pacsController.busy
                                        onClicked: browser.pacsController.selectSeries(seriesRow.modelData.uid, checked)
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: seriesRow.modelData.description || "未命名序列"
                                        color: Theme.textPrimary
                                        font.pixelSize: 13
                                        wrapMode: Text.Wrap
                                    }
                                    Caption {
                                        text: (seriesRow.modelData.instances || "—") + " 个实例"
                                    }
                                }
                            }
                            Text {
                                anchors.centerIn: parent
                                width: parent.width - 20
                                visible: browser.pacsController.series.length === 0
                                text: browser.pacsController.busy && browser.pacsController.operation === "series" ? "正在查询序列…" : "选择一个检查\n查看可导入的序列。"
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.Wrap
                                color: Theme.textSubtle
                                font.pixelSize: 12
                                lineHeight: 1.6
                            }
                        }
                    }
                }
                Components.AppButton {
                    objectName: "pacsImportSelected"
                    Layout.fillWidth: true
                    text: "导入所选（" + browser.pacsController.selectedCount + "）"
                    enabled: browser.pacsController.selectedCount > 0 && !browser.pacsController.busy
                    normalColor: Theme.primaryButtonBackground
                    onClicked: browser.pacsController.importSelected()
                }
            }
        }
        Item {
            visible: !browser.available
            Layout.fillWidth: true
            Layout.fillHeight: true
            ColumnLayout {
                anchors.centerIn: parent
                width: Math.min(420, parent.width - 24)
                spacing: 18
                Text {
                    Layout.fillWidth: true
                    text: "连接你的影像数据源"
                    color: Theme.textPrimary
                    font.pixelSize: 22
                    horizontalAlignment: Text.AlignHCenter
                }
                Text {
                    Layout.fillWidth: true
                    text: "先在设置中添加并启用一个 PACS 配置，\n即可在这里查询检查和导入序列。"
                    color: Theme.textMuted
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                    font.pixelSize: 13
                    lineHeight: 1.5
                }
                Components.AppButton {
                    objectName: "pacsConfigureEmpty"
                    Layout.alignment: Qt.AlignHCenter
                    text: "配置 PACS 数据源"
                    normalColor: Theme.primaryButtonBackground
                    onClicked: browser.workspaceController.openSettings()
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            visible: browser.pacsController.message !== "" || browser.pacsController.busy
            Text {
                objectName: "pacsBrowserMessage"
                Layout.fillWidth: true
                text: browser.pacsController.message
                color: browser.pacsController.isError ? Theme.dangerColor : Theme.textMuted
                wrapMode: Text.Wrap
                font.pixelSize: 12
            }
            Components.AppButton {
                objectName: "pacsCancel"
                visible: browser.pacsController.busy
                text: "取消"
                compact: true
                onClicked: browser.pacsController.cancel()
            }
        }
        Basic.ProgressBar {
            Layout.fillWidth: true
            visible: browser.pacsController.busy
            value: browser.pacsController.progress
            indeterminate: browser.pacsController.operation !== "import" || value === 0
        }
    }
}
