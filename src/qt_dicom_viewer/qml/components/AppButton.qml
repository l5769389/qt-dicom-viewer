pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Controls.Basic as Basic
import "../theme"

Basic.Button {
    id: control
    Layout.minimumWidth: 0

    property bool compact: false
    property bool momentary: false
    property string iconName: ""
    property real iconSize: 18
    property real minimumButtonWidth: 40
    property real cornerRadius: Theme.controlRadius
    property real fontPixelSize: 13
    property int fontWeight: Font.Normal

    property color normalColor: Theme.controlBackground
    property color hoverColor: Theme.controlHover
    property color pressedColor: Theme.controlPressed
    property color activeColor: Theme.selectionBackground
    property color disabledColor: Theme.controlDisabled
    property color textColor: Theme.textPrimary
    property color disabledTextColor: Theme.textDisabled
    property color focusBorderColor: Theme.focusBorder
    property color activeBorderColor: Theme.selectionBorder
    property color baseBorderColor: Theme.borderDefault
    property real baseBorderWidth: 0

    readonly property bool hasIcon:
        control.iconName !== "" || control.icon.source.toString() !== ""

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

    implicitHeight: compact ? Theme.compactControlHeight : Theme.controlHeight

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

        border.width: Math.max(
            control.baseBorderWidth,
            control.visualFocus ? 2 : control.checked ? 1 : 0
        )
        border.color: control.visualFocus ? control.focusBorderColor
            : control.checked ? control.activeBorderColor
            : control.baseBorderColor

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

            AppIcon {
                visible: control.iconName !== ""
                anchors.verticalCenter: parent.verticalCenter
                iconName: control.iconName
                iconSize: control.iconSize
                iconColor: control.enabled ? control.textColor : control.disabledTextColor
            }

            Image {
                visible: control.iconName === "" && control.hasIcon

                anchors.verticalCenter: parent.verticalCenter
                width: control.iconSize
                height: control.iconSize
                sourceSize.width: Math.ceil(control.iconSize * Math.max(1, Screen.devicePixelRatio))
                sourceSize.height: Math.ceil(control.iconSize * Math.max(1, Screen.devicePixelRatio))

                source: control.icon.source
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
                opacity: control.enabled ? 1 : 0.45
            }

            Label {
                visible: control.hasText

                anchors.verticalCenter: parent.verticalCenter
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
