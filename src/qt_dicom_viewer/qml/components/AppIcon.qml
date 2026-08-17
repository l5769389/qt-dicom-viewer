pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Shapes

Item {
    id: appIcon

    required property string iconName
    property real iconSize: 20
    property color iconColor: "#b8c3cf"

    readonly property bool isWindowLevelIcon: appIcon.iconName === "window"
    readonly property var mdiPathMap: ({
        "scroll": "M9,3L5,7H8V14H10V7H13M16,17V10H14V17H11L15,21L19,17H16Z",
        "slice-previous": "M7.41,15.41L12,10.83L16.59,15.41L18,14L12,8L6,14L7.41,15.41Z",
        "slice-next": "M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z",
        "cine-play": "M8,5.14V19.14L19,12.14L8,5.14Z",
        "cine-pause": "M14,19H18V5H14V19M6,19H10V5H6V19Z",
        "pan": "M13,6V11H18V7.75L22.25,12L18,16.25V13H13V18H16.25L12,22.25L7.75,18H11V13H6V16.25L1.75,12L6,7.75V11H11V6H7.75L12,1.75L16.25,6H13Z",
        "zoom": "M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22H20A2,2 0 0,0 22,20V12A10,10 0 0,0 12,2M13,7H11V11H7V13H11V17H13V13H17V11H13V7Z",
        "rotate": "M16.89,15.5L18.31,16.89C19.21,15.73 19.76,14.39 19.93,13H17.91C17.77,13.87 17.43,14.72 16.89,15.5M13,17.9V19.92C14.39,19.75 15.74,19.21 16.9,18.31L15.46,16.87C14.71,17.41 13.87,17.76 13,17.9M19.93,11C19.76,9.61 19.21,8.27 18.31,7.11L16.89,8.53C17.43,9.28 17.77,10.13 17.91,11M15.55,5.55L11,1V4.07C7.06,4.56 4,7.92 4,12C4,16.08 7.05,19.44 11,19.93V17.91C8.16,17.43 6,14.97 6,12C6,9.03 8.16,6.57 11,6.09V10L15.55,5.55Z",
        "pseudocolor-gray": "M12,19.58V19.58C10.4,19.58 8.89,18.96 7.76,17.83C6.62,16.69 6,15.19 6,13.58C6,12 6.62,10.47 7.76,9.34L12,5.1M17.66,7.93L12,2.27V2.27L6.34,7.93C3.22,11.05 3.22,16.12 6.34,19.24C7.9,20.8 9.95,21.58 12,21.58C14.05,21.58 16.1,20.8 17.66,19.24C20.78,16.12 20.78,11.05 17.66,7.93Z",
        "fullscreen": "M5,5H10V7H7V10H5V5M14,5H19V10H17V7H14V5M17,14H19V19H14V17H17V14M10,17V19H5V14H7V17H10Z",
        "reset": "M13,3A9,9 0 0,0 4,12H1L4.89,15.89L4.96,16.03L9,12H6A7,7 0 0,1 13,5A7,7 0 0,1 20,12A7,7 0 0,1 13,19C11.07,19 9.32,18.21 8.06,16.94L6.64,18.36C8.27,20 10.5,21 13,21A9,9 0 0,0 22,12A9,9 0 0,0 13,3Z",
        "measure": "M1.39,18.36L3.16,16.6L4.58,18L5.64,16.95L4.22,15.54L5.64,14.12L8.11,16.6L9.17,15.54L6.7,13.06L8.11,11.65L9.53,13.06L10.59,12L9.17,10.59L10.59,9.17L13.06,11.65L14.12,10.59L11.65,8.11L13.06,6.7L14.47,8.11L15.54,7.05L14.12,5.64L15.54,4.22L18,6.7L19.07,5.64L16.6,3.16L18.36,1.39L22.61,5.64L5.64,22.61L1.39,18.36Z",
        "measure-line": "M1.39,18.36L3.16,16.6L4.58,18L5.64,16.95L4.22,15.54L5.64,14.12L8.11,16.6L9.17,15.54L6.7,13.06L8.11,11.65L9.53,13.06L10.59,12L9.17,10.59L10.59,9.17L13.06,11.65L14.12,10.59L11.65,8.11L13.06,6.7L14.47,8.11L15.54,7.05L14.12,5.64L15.54,4.22L18,6.7L19.07,5.64L16.6,3.16L18.36,1.39L22.61,5.64L5.64,22.61L1.39,18.36Z",
        "measure-angle": "M20,19H4.09L14.18,4.43L15.82,5.57L11.28,12.13C12.89,12.96 14,14.62 14,16.54C14,16.7 14,16.85 13.97,17H20V19M7.91,17H11.96C12,16.85 12,16.7 12,16.54C12,15.28 11.24,14.22 10.14,13.78L7.91,17Z",
        "measure-rect": "M4,6V19H20V6H4M18,17H6V8H18V17Z",
        "measure-ellipse": "M12,6C16.41,6 20,8.69 20,12C20,15.31 16.41,18 12,18C7.59,18 4,15.31 4,12C4,8.69 7.59,6 12,6M12,4C6.5,4 2,7.58 2,12C2,16.42 6.5,20 12,20C17.5,20 22,16.42 22,12C22,7.58 17.5,4 12,4Z",
        "annotate": "M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z",
        "help": "M11,18H13V16H11V18M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,12 11,11.75 11,15H13C13,12.75 16,12.5 16,10A4,4 0 0,0 12,6Z"
    })
    readonly property string pathData: appIcon.mdiPathMap[appIcon.iconName]
        ?? appIcon.mdiPathMap.help

    implicitWidth: appIcon.iconSize
    implicitHeight: appIcon.iconSize
    width: appIcon.iconSize
    height: appIcon.iconSize

    Shape {
        visible: !appIcon.isWindowLevelIcon
        width: 24
        height: 24

        transform: Scale {
            xScale: appIcon.width / 24
            yScale: appIcon.height / 24
        }

        ShapePath {
            fillColor: appIcon.iconColor
            strokeColor: "transparent"

            PathSvg {
                path: appIcon.pathData
            }
        }
    }

    Canvas {
        id: windowLevelCanvas

        anchors.fill: parent
        visible: appIcon.isWindowLevelIcon

        onPaint: {
            const context = getContext("2d")
            context.reset()

            const scale = Math.min(width, height) / 24
            const centerX = width / 2
            const centerY = height / 2
            const gradient = context.createLinearGradient(
                centerX - 8.25 * scale,
                centerY,
                centerX + 8.25 * scale,
                centerY
            )
            gradient.addColorStop(0, "#ffffff")
            gradient.addColorStop(1, "#000000")

            context.beginPath()
            context.arc(centerX, centerY, 8.25 * scale, 0, Math.PI * 2)
            context.fillStyle = gradient
            context.fill()

            context.beginPath()
            context.arc(centerX, centerY, 9.25 * scale, 0, Math.PI * 2)
            context.lineWidth = 1.5 * scale
            context.strokeStyle = appIcon.iconColor
            context.stroke()
        }

        Connections {
            target: appIcon

            function onIconColorChanged() {
                windowLevelCanvas.requestPaint()
            }

            function onWidthChanged() {
                windowLevelCanvas.requestPaint()
            }

            function onHeightChanged() {
                windowLevelCanvas.requestPaint()
            }
        }
    }
}
