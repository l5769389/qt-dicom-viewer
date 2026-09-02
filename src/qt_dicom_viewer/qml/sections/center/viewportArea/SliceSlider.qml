pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import "../../../theme"

Item {
    id: root

    required property var viewportController

    implicitWidth: 30
    visible: root.viewportController
        && root.viewportController.viewportType === "stack"
        && root.viewportController.sliceCount > 1

    Rectangle {
        anchors.fill: parent
        color: Theme.panelBackgroundSoft

        Rectangle {
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            width: 1
            color: Theme.dividerColor
        }
    }

    Basic.Slider {
        id: sliceControl

        anchors.fill: parent
        anchors.topMargin: 10
        anchors.bottomMargin: 10
        anchors.leftMargin: 7
        anchors.rightMargin: 7

        orientation: Qt.Vertical
        from: 0
        to: root.viewportController
            ? Math.max(0, root.viewportController.sliceCount - 1)
            : 0
        stepSize: 1
        snapMode: Basic.Slider.SnapAlways
        live: true
        value: root.viewportController
            ? root.viewportController.sliceIndex
            : 0

        onMoved: {
            if (!root.viewportController)
                return
            root.viewportController.setSliceIndex(
                Math.round(sliceControl.value)
            )
        }

        Basic.ToolTip.visible: sliceControl.hovered || sliceControl.pressed
        Basic.ToolTip.delay: 250
        Basic.ToolTip.text: Math.round(sliceControl.value) + 1
            + " / " + (root.viewportController
                ? root.viewportController.sliceCount
                : 0)

        background: Rectangle {
            x: sliceControl.leftPadding
                + (sliceControl.availableWidth - width) / 2
            y: sliceControl.topPadding
            width: 4
            height: sliceControl.availableHeight
            radius: 2
            color: Theme.controlBackground
            border.width: 1
            border.color: Theme.controlBorder

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: (1.0 - sliceControl.visualPosition)
                    * parent.height
                radius: parent.radius
                color: Theme.primaryStrong
            }
        }

        handle: Rectangle {
            x: sliceControl.leftPadding
                + (sliceControl.availableWidth - width) / 2
            y: sliceControl.topPadding
                + sliceControl.visualPosition
                    * (sliceControl.availableHeight - height)
            implicitWidth: 14
            implicitHeight: 14
            radius: width / 2
            color: sliceControl.pressed
                ? Theme.primaryPressed
                : sliceControl.hovered
                    ? Theme.primaryHover
                    : Theme.primaryColor
            border.width: 1
            border.color: Theme.textOnPrimary
        }
    }
}
