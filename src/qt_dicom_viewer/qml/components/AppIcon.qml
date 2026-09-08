pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Shapes
import QtQuick.Window
import "../theme"

Item {
    id: appIcon

    required property string iconName
    property real iconSize: 20
    property color iconColor: Theme.iconDefault
    property color detailColor: "transparent"
    readonly property real pixelRatio: Math.max(1, Screen.devicePixelRatio)

    readonly property bool isNavigationIcon: iconName.startsWith("nav-") || iconName === "fusion"
    readonly property bool isSvgIcon: isNavigationIcon || ["manual", "annotate-arrow", "annotate-text", "delete", "clear", "crop-inside", "crop-outside", "save", "window", "scroll", "pan", "zoom", "measure", "measure-line", "measure-angle", "measure-rect", "measure-ellipse", "rotate", "rotate-3d", "rotate-cw90", "rotate-ccw90", "mirror-h", "mirror-v", "mip", "annotate", "viewport-settings", "service", "mtf", "qa", "remove-bed", "volume-crop", "palette", "cine-play", "cine-pause", "reset", "export", "export-png", "export-dicom", "segmentation", "voi", "invert"].includes(iconName)
    readonly property bool isPseudocolorIcon: ["pseudocolor", "pseudocolor-gray"].includes(iconName)
    readonly property string rasterSource: ""
    readonly property var mdiPathMap: ({
        "pet-window": "M3,3H5V19H22V21H3ZM6,15C9,15 8,7 11,7C14,7 13,17 16,17C18,17 18,12 21,12V14C19,14 20,19 16,19C11,19 12,9 11,9C10,9 11,17 6,17ZM15,3H22V5H15ZM18,2H20V8H18Z",
        "registration": "M3,2H9V4H5V8H3ZM15,2H21V8H19V4H15ZM3,16H5V20H9V22H3ZM19,16H21V22H15V20H19ZM11,6H13V11H18V13H13V18H11V13H6V11H11Z",
        "chevron-down": "M6,9L12,15L18,9L16.6,7.6L12,12.2L7.4,7.6Z",
        "check": "M9,16.2L4.8,12L3.4,13.4L9,19L21,7L19.6,5.6Z",
        "settings": "M19.4,13A7.6,7.6 0 0,0 19.4,11L21.5,9.4L19.5,6L17,7A7.6,7.6 0 0,0 15.3,6L15,3H9L8.7,6A7.6,7.6 0 0,0 7,7L4.5,6L2.5,9.4L4.6,11A7.6,7.6 0 0,0 4.6,13L2.5,14.6L4.5,18L7,17A7.6,7.6 0 0,0 8.7,18L9,21H15L15.3,18A7.6,7.6 0 0,0 17,17L19.5,18L21.5,14.6ZM12,8A4,4 0 1,1 12,16A4,4 0 1,1 12,8Z",
        "volume-bed": "M3,4H5V13H21V15H5V19H3V4M7,8H11V11H7V8M13,7H19A2,2 0 0,1 21,9V11H13V7M8,18H21V20H8V18Z",
        "slice-previous": "M7.41,15.41L12,10.83L16.59,15.41L18,14L12,8L6,14L7.41,15.41Z",
        "slice-next": "M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z",
        "rotate-3d-variant": "M12,5C16.97,5 21,7.69 21,11C21,12.68 19.96,14.2 18.29,15.29C19.36,14.42 20,13.32 20,12.13C20,9.29 16.42,7 12,7V10L8,6L12,2V5M12,19C7.03,19 3,16.31 3,13C3,11.32 4.04,9.8 5.71,8.71C4.64,9.58 4,10.68 4,11.88C4,14.71 7.58,17 12,17V14L16,18L12,22V19Z",
        "pseudocolor-gray": "M12,19.58V19.58C10.4,19.58 8.89,18.96 7.76,17.83C6.62,16.69 6,15.19 6,13.58C6,12 6.62,10.47 7.76,9.34L12,5.1M17.66,7.93L12,2.27V2.27L6.34,7.93C3.22,11.05 3.22,16.12 6.34,19.24C7.9,20.8 9.95,21.58 12,21.58C14.05,21.58 16.1,20.8 17.66,19.24C20.78,16.12 20.78,11.05 17.66,7.93Z",
        "fullscreen": "M5,5H10V7H7V10H5V5M14,5H19V10H17V7H14V5M17,14H19V19H14V17H17V14M10,17V19H5V14H7V17H10Z",
        "view-tile": "M3,3H10V10H3V3M14,3H21V10H14V3M3,14H10V21H3V14M14,14H21V21H14V14Z",
        "folder": "M10,4H2C0.89,4 0,4.89 0,6V18C0,19.1 0.9,20 2,20H22C23.1,20 24,19.1 24,18V8C24,6.89 23.1,6 22,6H12L10,4Z",
        "shield": "M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1M12,3.18L19,6.3V11C19,15.52 16.02,19.69 12,20.93C7.98,19.69 5,15.52 5,11V6.3L12,3.18Z",
        "close": "M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",
        "help": "M11,18H13V16H11V18M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,12 11,11.75 11,15H13C13,12.75 16,12.5 16,10A4,4 0 0,0 12,6Z"
    })
    readonly property string pathData: appIcon.mdiPathMap[appIcon.iconName]
        ?? appIcon.mdiPathMap.help

    implicitWidth: appIcon.iconSize
    implicitHeight: appIcon.iconSize
    width: appIcon.iconSize
    height: appIcon.iconSize

    Shape {
        visible: !appIcon.isSvgIcon && !appIcon.isPseudocolorIcon
        width: 24; height: 24
        transform: Scale { xScale: appIcon.width / 24; yScale: appIcon.height / 24 }
        ShapePath { fillColor: appIcon.iconColor; strokeColor: "transparent"; PathSvg { path: appIcon.pathData } }
    }
    Image {
        objectName: "navigationSvgIcon"
        anchors.fill: parent
        visible: appIcon.isSvgIcon
        source: visible ? "image://navigation/" + appIcon.iconName + "/"
            + encodeURIComponent(appIcon.iconColor.toString()) + "/" + encodeURIComponent(appIcon.detailColor.toString()) : ""
        sourceSize.width: Math.ceil(appIcon.width * appIcon.pixelRatio)
        sourceSize.height: Math.ceil(appIcon.height * appIcon.pixelRatio)
        smooth: true
    }
    ColorMapIcon {
        objectName: "pseudocolorIcon"
        anchors.fill: parent
        visible: appIcon.isPseudocolorIcon
        tint: appIcon.iconColor
    }
}
