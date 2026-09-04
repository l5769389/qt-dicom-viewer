pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Shapes

Item {
    id: appIcon

    required property string iconName
    property real iconSize: 20
    property color iconColor: "#b8c3cf"

    readonly property bool isWindowLevelIcon: appIcon.iconName === "window"
    readonly property bool isTintableRasterIcon: appIcon.iconName === "mip"
    // 复杂图标直接使用生成的 PNG，不再通过矢量路径重绘。
    readonly property var rasterSourceMap: ({
        "service": "../assets/icons/service.png",
        "mtf": "../assets/icons/mtf.png",
        "qa": "../assets/icons/qa.png",
        "mip": "../assets/icons/mip.png"
    })
    readonly property string rasterSource: appIcon.rasterSourceMap[appIcon.iconName] ?? ""
    readonly property var mdiPathMap: ({
        "palette": "M12,3C7.03,3 3,7.03 3,12C3,16.97 7.03,21 12,21H13.5C14.88,21 16,19.88 16,18.5C16,17.87 15.76,17.3 15.38,16.86C15.13,16.58 15,16.26 15,16C15,15.45 15.45,15 16,15H18C20.21,15 22,13.21 22,11C22,6.58 17.52,3 12,3M7,13A1.5,1.5 0 1,1 7,10A1.5,1.5 0 1,1 7,13M9.5,8.5A1.5,1.5 0 1,1 9.5,5.5A1.5,1.5 0 1,1 9.5,8.5M14,8A1.5,1.5 0 1,1 14,5A1.5,1.5 0 1,1 14,8M18,11A1.5,1.5 0 1,1 18,8A1.5,1.5 0 1,1 18,11Z",
        "scroll": "M9,3L5,7H8V14H10V7H13M16,17V10H14V17H11L15,21L19,17H16Z",
        "slice-previous": "M7.41,15.41L12,10.83L16.59,15.41L18,14L12,8L6,14L7.41,15.41Z",
        "slice-next": "M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z",
        "cine-play": "M8,5.14V19.14L19,12.14L8,5.14Z",
        "cine-pause": "M14,19H18V5H14V19M6,19H10V5H6V19Z",
        "pan": "M13,6V11H18V7.75L22.25,12L18,16.25V13H13V18H16.25L12,22.25L7.75,18H11V13H6V16.25L1.75,12L6,7.75V11H11V6H7.75L12,1.75L16.25,6H13Z",
        "zoom": "M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22H20A2,2 0 0,0 22,20V12A10,10 0 0,0 12,2M13,7H11V11H7V13H11V17H13V13H17V11H13V7Z",
        "rotate": "M16.89,15.5L18.31,16.89C19.21,15.73 19.76,14.39 19.93,13H17.91C17.77,13.87 17.43,14.72 16.89,15.5M13,17.9V19.92C14.39,19.75 15.74,19.21 16.9,18.31L15.46,16.87C14.71,17.41 13.87,17.76 13,17.9M19.93,11C19.76,9.61 19.21,8.27 18.31,7.11L16.89,8.53C17.43,9.28 17.77,10.13 17.91,11M15.55,5.55L11,1V4.07C7.06,4.56 4,7.92 4,12C4,16.08 7.05,19.44 11,19.93V17.91C8.16,17.43 6,14.97 6,12C6,9.03 8.16,6.57 11,6.09V10L15.55,5.55Z",
        "rotate-3d": "M7.47,21.5C4.2,19.94 1.86,16.76 1.5,13H0C0.5,19.16 5.66,24 11.95,24L12.61,23.97L8.8,20.16L7.47,21.5M8.36,14.96C8.17,14.96 8,14.93 7.84,14.88C7.68,14.82 7.55,14.75 7.44,14.64C7.33,14.54 7.24,14.42 7.18,14.27C7.12,14.13 7.09,13.97 7.09,13.8H5.79C5.79,14.16 5.86,14.5 6,14.75C6.14,15 6.33,15.25 6.56,15.44C6.8,15.62 7.07,15.76 7.38,15.85C7.68,15.95 8,16 8.34,16C8.71,16 9.06,15.95 9.37,15.85C9.69,15.75 9.97,15.6 10.2,15.41C10.43,15.22 10.62,15 10.75,14.69C10.88,14.4 10.95,14.08 10.95,13.72C10.95,13.53 10.93,13.34 10.88,13.16C10.83,13 10.76,12.81 10.65,12.65C10.55,12.5 10.41,12.35 10.25,12.22C10.08,12.09 9.88,12 9.64,11.91C9.84,11.82 10,11.71 10.16,11.58C10.31,11.45 10.43,11.31 10.53,11.16C10.63,11 10.7,10.86 10.75,10.7C10.8,10.54 10.82,10.38 10.82,10.22C10.82,9.86 10.76,9.54 10.64,9.26C10.5,9 10.35,8.75 10.13,8.57C9.93,8.38 9.66,8.24 9.36,8.14C9.05,8.05 8.71,8 8.34,8C8,8 7.65,8.05 7.34,8.16C7.04,8.27 6.77,8.42 6.55,8.61C6.34,8.8 6.17,9 6.04,9.28C5.92,9.54 5.86,9.82 5.86,10.13H7.16C7.16,9.96 7.19,9.81 7.25,9.68C7.31,9.55 7.39,9.43 7.5,9.34C7.61,9.25 7.73,9.17 7.88,9.12C8.03,9.07 8.18,9.04 8.36,9.04C8.76,9.04 9.06,9.14 9.25,9.35C9.44,9.55 9.54,9.84 9.54,10.21C9.54,10.39 9.5,10.55 9.46,10.7C9.41,10.85 9.32,10.97 9.21,11.07C9.1,11.17 8.96,11.25 8.8,11.31C8.64,11.37 8.44,11.4 8.22,11.4H7.45V12.43H8.22C8.44,12.43 8.64,12.45 8.82,12.5C9,12.55 9.15,12.63 9.27,12.73C9.39,12.84 9.5,12.97 9.56,13.13C9.63,13.29 9.66,13.5 9.66,13.7C9.66,14.11 9.54,14.42 9.31,14.63C9.08,14.86 8.76,14.96 8.36,14.96M16.91,9.04C16.59,8.71 16.21,8.45 15.77,8.27C15.34,8.09 14.85,8 14.31,8H11.95V16H14.25C14.8,16 15.31,15.91 15.76,15.73C16.21,15.55 16.6,15.3 16.92,14.97C17.24,14.64 17.5,14.24 17.66,13.78C17.83,13.31 17.92,12.79 17.92,12.21V11.81C17.92,11.23 17.83,10.71 17.66,10.24C17.5,9.77 17.23,9.37 16.91,9.04M16.5,12.2C16.5,12.62 16.47,13 16.38,13.33C16.28,13.66 16.14,13.95 15.95,14.18C15.76,14.41 15.5,14.59 15.24,14.71C14.95,14.83 14.62,14.89 14.25,14.89H13.34V9.12H14.31C15.03,9.12 15.58,9.35 15.95,9.81C16.33,10.27 16.5,10.93 16.5,11.8M11.95,0L11.29,0.03L15.1,3.84L16.43,2.5C19.7,4.06 22.04,7.23 22.39,11H23.89C23.39,4.84 18.24,0 11.95,0Z",
        "rotate-3d-variant": "M12,5C16.97,5 21,7.69 21,11C21,12.68 19.96,14.2 18.29,15.29C19.36,14.42 20,13.32 20,12.13C20,9.29 16.42,7 12,7V10L8,6L12,2V5M12,19C7.03,19 3,16.31 3,13C3,11.32 4.04,9.8 5.71,8.71C4.64,9.58 4,10.68 4,11.88C4,14.71 7.58,17 12,17V14L16,18L12,22V19Z",
        "rotate-cw90": "M10,4V1L14,5L10,9V6A6,6 0 0,0 4,12L4.08,13H2.06L2,12A8,8 0 0,1 10,4M17,2H20A2,2 0 0,1 22,4V20A2,2 0 0,1 20,22H17A2,2 0 0,1 15,20V4A2,2 0 0,1 17,2M4,15H13V22H4A2,2 0 0,1 2,20V17A2,2 0 0,1 4,15Z",
        "rotate-ccw90": "M4,2H7A2,2 0 0,1 9,4V20A2,2 0 0,1 7,22H4A2,2 0 0,1 2,20V4A2,2 0 0,1 4,2M20,15A2,2 0 0,1 22,17V20A2,2 0 0,1 20,22H11V15H20M14,4A8,8 0 0,1 22,12L21.94,13H19.92L20,12A6,6 0 0,0 14,6V9L10,5L14,1V4Z",
        "mirror-h": "M15 21H17V19H15M19 9H21V7H19M3 5V19C3 20.1 3.9 21 5 21H9V19H5V5H9V3H5C3.9 3 3 3.9 3 5M19 3V5H21C21 3.9 20.1 3 19 3M11 23H13V1H11M19 17H21V15H19M15 5H17V3H15M19 13H21V11H19M19 21C20.1 21 21 20.1 21 19H19Z",
        "mirror-v": "M3 15V17H5V15M15 19V21H17V19M19 3H5C3.9 3 3 3.9 3 5V9H5V5H19V9H21V5C21 3.9 20.1 3 19 3M21 19H19V21C20.1 21 21 20.1 21 19M1 11V13H23V11M7 19V21H9V19M19 15V17H21V15M11 19V21H13V19M3 19C3 20.1 3.9 21 5 21V19Z",
        "pseudocolor-gray": "M12,19.58V19.58C10.4,19.58 8.89,18.96 7.76,17.83C6.62,16.69 6,15.19 6,13.58C6,12 6.62,10.47 7.76,9.34L12,5.1M17.66,7.93L12,2.27V2.27L6.34,7.93C3.22,11.05 3.22,16.12 6.34,19.24C7.9,20.8 9.95,21.58 12,21.58C14.05,21.58 16.1,20.8 17.66,19.24C20.78,16.12 20.78,11.05 17.66,7.93Z",
        "viewport-settings": "M12,9C10.34,9 9,10.34 9,12C9,13.66 10.34,15 12,15C13.66,15 15,13.66 15,12C15,10.34 13.66,9 12,9M12,4.5C17,4.5 21.27,7.61 23,12C21.27,16.39 17,19.5 12,19.5C7,19.5 2.73,16.39 1,12C2.73,7.61 7,4.5 12,4.5M3.18,12C4.83,15.36 8.24,17.5 12,17.5C15.76,17.5 19.17,15.36 20.82,12C19.17,8.64 15.76,6.5 12,6.5C8.24,6.5 4.83,8.64 3.18,12Z",
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
        visible: !appIcon.isWindowLevelIcon && appIcon.rasterSource === ""
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

    Image {
        objectName: "rasterToolIcon"
        anchors.fill: parent
        visible: appIcon.rasterSource !== ""
            && !appIcon.isTintableRasterIcon
        source: appIcon.rasterSource
        // 保留原图高分辨率供高 DPI 缩放使用，由 Qt 缓存解码结果。
        fillMode: Image.PreserveAspectFit
        smooth: true
        mipmap: true
    }

    Canvas {
        id: tintedRasterIcon
        objectName: "tintedRasterToolIcon"

        anchors.fill: parent
        visible: appIcon.rasterSource !== ""
            && appIcon.isTintableRasterIcon
        readonly property color tintColor: appIcon.iconColor
        // 原始 PNG 留有透明安全边距，轻微放大后可与 24x24
        // MDI 图标在同一个 22px 容器内保持一致的视觉尺寸。
        readonly property real rasterScale: 1.14

        function ensureImageLoaded() {
            if (visible && appIcon.rasterSource !== "")
                loadImage(appIcon.rasterSource)
        }

        Component.onCompleted: ensureImageLoaded()
        onVisibleChanged: ensureImageLoaded()
        onImageLoaded: requestPaint()

        onPaint: {
            const context = getContext("2d")
            context.reset()
            if (!isImageLoaded(appIcon.rasterSource)) {
                ensureImageLoaded()
                return
            }

            const drawWidth = width * rasterScale
            const drawHeight = height * rasterScale
            context.drawImage(
                appIcon.rasterSource,
                (width - drawWidth) / 2,
                (height - drawHeight) / 2,
                drawWidth,
                drawHeight
            )
            context.globalCompositeOperation = "source-in"
            context.fillStyle = appIcon.iconColor
            context.fillRect(0, 0, width, height)
            context.globalCompositeOperation = "source-over"
        }

        Connections {
            target: appIcon

            function onIconColorChanged() {
                tintedRasterIcon.requestPaint()
            }

            function onWidthChanged() {
                tintedRasterIcon.requestPaint()
            }

            function onHeightChanged() {
                tintedRasterIcon.requestPaint()
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
