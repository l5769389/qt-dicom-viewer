import QtQuick
import "../theme"

MouseArea {
    id: handle
    property real currentWidth: 0
    property real minimumWidth: 0
    property real maximumWidth: 1000
    property real direction: 1
    property real pressX: 0
    property real pressWidth: 0
    property real candidateWidth: currentWidth
    signal widthDragged(real value)
    signal widthCommitted(real value)
    implicitWidth: 8
    hoverEnabled: true
    cursorShape: Qt.SizeHorCursor
    preventStealing: true
    onPressed: mouse => {
        pressX = mapToItem(null, mouse.x, mouse.y).x
        pressWidth = currentWidth
        candidateWidth = currentWidth
    }
    onPositionChanged: mouse => {
        if (!pressed) return
        candidateWidth = Math.max(minimumWidth, Math.min(maximumWidth,
            pressWidth + direction * (mapToItem(null, mouse.x, mouse.y).x - pressX)))
        widthDragged(candidateWidth)
    }
    onReleased: widthCommitted(candidateWidth)
    onCanceled: widthCommitted(candidateWidth)
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        width: 1
        height: parent.height
        color: handle.containsMouse || handle.pressed ? Theme.primaryColor : Theme.dividerColor
    }
}
