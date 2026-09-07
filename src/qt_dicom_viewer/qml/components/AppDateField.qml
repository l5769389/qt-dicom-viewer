pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../theme"
AppTextField {
    id: root
    rightPadding: 32
    placeholderText: "YYYY-MM-DD"
    Accessible.name: "日期"
    readonly property bool validDate: {
        if (!text) return true
        if (!/^\d{4}-\d{2}-\d{2}$/.test(text)) return false
        const parts = text.split("-").map(Number)
        const d = new Date(parts[0], parts[1] - 1, parts[2])
        return d.getFullYear() === parts[0] && d.getMonth() === parts[1] - 1 && d.getDate() === parts[2]
    }
    color: validDate ? Theme.textPrimary : Theme.dangerColor
    function chooseDate(d) {
        text = d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0")
        calendar.close()
    }
    AppButton {
        objectName: root.objectName + "-calendar"
        anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
        width: 28; height: 28; minimumButtonWidth: 28; compact: true
        text: "▦"; Accessible.name: "选择日期"; normalColor: "transparent"
        onClicked: calendar.open()
    }
    Basic.Popup {
        id: calendar
        objectName: root.objectName + "-popup"
        parent: Basic.Overlay.overlay
        x: Math.max(8, Math.min(parent.width - width - 8, root.mapToItem(parent, 0, 0).x))
        y: Math.max(8, Math.min(parent.height - height - 8, root.mapToItem(parent, 0, root.height).y))
        width: Math.min(292, parent.width - 16)
        padding: 10; modal: true; focus: true
        Basic.Overlay.modal: Rectangle { color: "#88000000" }
        property date displayed: new Date()
        onOpened: {
            if (root.text && root.validDate) {
                const p = root.text.split("-").map(Number)
                displayed = new Date(p[0], p[1] - 1, 1)
            } else displayed = new Date()
        }
        function moveMonth(amount) { displayed = new Date(displayed.getFullYear(), displayed.getMonth() + amount, 1) }
        background: Rectangle { color: Theme.panelBackground; border.color: Theme.borderStrong; radius: 6 }
        contentItem: ColumnLayout {
            spacing: 8
            RowLayout {
                Layout.fillWidth: true
                AppButton { text: "‹"; minimumButtonWidth: 24; compact: true; Accessible.name: "上个月"; onClicked: calendar.moveMonth(-1) }
                AppNumberField {
                    objectName: root.objectName + "-year"
                    Layout.fillWidth: true; Layout.minimumWidth: 55
                    minimum: 1900; maximum: 2200; decimals: 0
                    horizontalAlignment: Text.AlignHCenter
                    numberValue: calendar.displayed.getFullYear()
                    Accessible.name: "年份"
                    onEdited: value => calendar.displayed = new Date(value, calendar.displayed.getMonth(), 1)
                }
                AppComboBox {
                    objectName: root.objectName + "-month"
                    Layout.preferredWidth: 74
                    model: ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
                    currentIndex: calendar.displayed.getMonth()
                    onActivated: index => calendar.displayed = new Date(calendar.displayed.getFullYear(), index, 1)
                }
                AppButton { text: "›"; minimumButtonWidth: 24; compact: true; Accessible.name: "下个月"; onClicked: calendar.moveMonth(1) }
            }
            GridLayout {
                Layout.fillWidth: true; columns: 7; columnSpacing: 2; rowSpacing: 2; uniformCellWidths: true
                Repeater {
                    model: ["一", "二", "三", "四", "五", "六", "日"]
                    Text { required property string modelData; Layout.fillWidth: true; text: modelData; horizontalAlignment: Text.AlignHCenter; color: Theme.textMuted; font.pixelSize: 11 }
                }
                Repeater {
                    model: 42
                    AppButton {
                        required property int index
                        readonly property date day: new Date(calendar.displayed.getFullYear(), calendar.displayed.getMonth(), 1 + index - (new Date(calendar.displayed.getFullYear(), calendar.displayed.getMonth(), 1).getDay() + 6) % 7)
                        objectName: root.objectName + "-day-" + day.getDate() + (day.getMonth() === calendar.displayed.getMonth() ? "" : "-outside")
                        Layout.fillWidth: true; Layout.preferredHeight: 28; minimumButtonWidth: 24; compact: true
                        checked: root.text === day.getFullYear() + "-" + String(day.getMonth() + 1).padStart(2, "0") + "-" + String(day.getDate()).padStart(2, "0")
                        text: day.getDate()
                        textColor: day.getMonth() === calendar.displayed.getMonth() ? Theme.textPrimary : Theme.textSubtle
                        onClicked: root.chooseDate(day)
                    }
                }
            }
            RowLayout {
                AppButton { text: "今天"; compact: true; onClicked: root.chooseDate(new Date()) }
                Item { Layout.fillWidth: true }
                AppButton { objectName: root.objectName + "-clear"; text: "清空"; compact: true; onClicked: { root.text = ""; calendar.close() } }
            }
        }
    }
}
