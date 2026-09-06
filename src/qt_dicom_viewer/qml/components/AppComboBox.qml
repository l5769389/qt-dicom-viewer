import QtQuick
import QtQuick.Controls.Basic as Basic
import "../theme"

Basic.ComboBox {
    id: control
    implicitHeight: 38
    leftPadding: 12
    rightPadding: 28
    font.pixelSize: 13
    contentItem: Text {
        text: control.displayText
        color: control.enabled ? Theme.textPrimary : Theme.textDisabled
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        font: control.font
    }
    indicator: Text {
        x: control.width - 23
        anchors.verticalCenter: parent.verticalCenter
        text: "⌄"
        color: Theme.textMuted
    }
    background: Rectangle {
        color: Theme.controlBackground
        border.color: control.activeFocus ? Theme.focusBorder : Theme.borderDefault
        radius: 7
    }
    delegate: Basic.ItemDelegate {
        required property int index
        required property var modelData
        width: control.width
        text: control.textRole ? modelData[control.textRole] : modelData
        highlighted: control.highlightedIndex === index
        contentItem: Text {
            text: parent.text
            color: Theme.textPrimary
            elide: Text.ElideRight
            font.pixelSize: 13
        }
        background: Rectangle {
            color: parent.highlighted ? Theme.selectionBackground : Theme.cardBackground
        }
    }
    popup: Basic.Popup {
        y: control.height + 4
        width: control.width
        implicitHeight: Math.min(contentItem.implicitHeight + 8, 320)
        padding: 4
        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            Basic.ScrollBar.vertical: Basic.ScrollBar {}
        }
        background: Rectangle {
            color: Theme.cardBackground
            border.color: Theme.borderStrong
            radius: 7
        }
    }
}
