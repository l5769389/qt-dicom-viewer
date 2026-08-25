pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Basic as Basic

Basic.Button {
    id: control

    property bool compact: false
    property bool momentary: false
    property real iconSize: 18
    property real minimumButtonWidth: 40
    property real cornerRadius: 6
    property real fontPixelSize: 13
    property int fontWeight: Font.Normal

    property color normalColor: "#202833"
    property color hoverColor: "#293545"
    property color pressedColor: "#18202a"
    property color activeColor: "#273f55"
    property color disabledColor: "#191e25"
    property color textColor: "#e8edf3"
    property color disabledTextColor: "#68717d"
    property color focusBorderColor: "#49b9ed"
    property color activeBorderColor: "#4f9ad2"

    readonly property bool hasIcon:
        control.icon.source.toString() !== ""

    readonly property bool hasText:
        control.text.length > 0

    hoverEnabled: true
    focusPolicy: control.momentary
        ? Qt.TabFocus
        : Qt.StrongFocus

    leftPadding: compact ? 6 : 12
    rightPadding: compact ? 6 : 12
    topPadding: compact ? 6 : 8
    bottomPadding: compact ? 6 : 8

    implicitWidth: Math.max(
        minimumButtonWidth,
        contentRow.implicitWidth + leftPadding + rightPadding
    )

    implicitHeight: compact ? 34 : 38

    background: Rectangle {
        radius: control.cornerRadius

        color: {
            if (!control.enabled)
                return control.disabledColor
            if (control.down)
                return control.pressedColor
            if (control.checked)
                return control.activeColor
            if (control.hovered)
                return control.hoverColor
            return control.normalColor
        }

        border.width: control.activeFocus || control.checked ? 1 : 0
        border.color: control.checked
            ? control.activeBorderColor
            : control.focusBorderColor

        Behavior on color {
            ColorAnimation { duration: 90 }
        }
    }

    contentItem: Item {
        implicitWidth: contentRow.implicitWidth
        implicitHeight: contentRow.implicitHeight

        Row {
            id: contentRow

            anchors.centerIn: parent
            spacing: control.hasIcon && control.hasText ? 7 : 0

            Image {
                visible: control.hasIcon

                width: control.iconSize
                height: control.iconSize
                sourceSize.width: control.iconSize
                sourceSize.height: control.iconSize

                source: control.icon.source
                fillMode: Image.PreserveAspectFit
                opacity: control.enabled ? 1 : 0.45
            }

            Label {
                visible: control.hasText

                text: control.text
                color: control.enabled
                    ? control.textColor
                    : control.disabledTextColor

                font.pixelSize: control.fontPixelSize
                font.weight: control.checked
                    ? Font.DemiBold
                    : control.fontWeight

                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}
