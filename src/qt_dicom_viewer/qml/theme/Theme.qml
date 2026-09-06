pragma Singleton

import QtQuick

QtObject {
    // Brand colors: cold cyan is the main interaction color, while steel blue
    // is used for neutral secondary actions. Warm orange is intentionally rare.
    readonly property color primaryColor: "#66d0ff"
    readonly property color primaryStrong: "#2a95e4"
    readonly property color primaryHover: "#7bd8ff"
    readonly property color primaryPressed: "#237fbd"
    readonly property color primarySoft: "#17354a"
    readonly property color primarySoftHover: "#1d425b"

    readonly property color secondaryColor: "#91a4b6"
    readonly property color secondaryStrong: "#61768a"
    readonly property color secondaryHover: "#a8bac9"
    readonly property color secondaryPressed: "#4d6072"
    readonly property color secondarySoft: "#28323c"

    readonly property color accentWarm: "#ff8a5b"

    // Surface hierarchy. Keep the DICOM canvas darker than application chrome.
    readonly property color appBackground: "#101317"
    readonly property color shellBackground: "#101317"
    readonly property color panelBackground: "#171c22"
    readonly property color panelBackgroundSoft: "#14191f"
    readonly property color panelBackgroundStrong: "#1b2128"
    readonly property color workspaceBackground: "#0c0f13"
    readonly property color canvasBackground: "#050709"
    readonly property color cardBackground: "#1d242c"
    readonly property color cardBackgroundHover: "#252e38"
    readonly property color elevatedBackground: "#29333e"

    // Borders and separators.
    readonly property color borderSubtle: "#29313a"
    readonly property color borderDefault: "#36414d"
    readonly property color borderStrong: "#566675"
    readonly property color dividerColor: "#303a45"
    readonly property color focusBorder: primaryColor

    // Typography.
    readonly property color textPrimary: "#edf1f5"
    readonly property color textSecondary: "#c3ccd5"
    readonly property color textMuted: "#a1adb9"
    readonly property color textSubtle: "#909daa"
    readonly property color textDisabled: "#73808c"
    readonly property color textOnPrimary: "#f8fbff"
    readonly property color overlayText: "#eaf3fb"
    readonly property color overlayOutline: "#cc000000"

    // Generic controls.
    readonly property color controlBackground: "#202831"
    readonly property color controlHover: "#2b3743"
    readonly property color controlPressed: "#17212b"
    readonly property color controlDisabled: "#1b2128"
    readonly property color controlBorder: "#3a4856"
    readonly property color controlHoverBorder: "#758b9d"

    // Selection / active interaction. A selected item is not a status message.
    readonly property color selectionBackground: "#203b4c"
    readonly property color selectionHover: "#28485b"
    readonly property color selectionBorder: "#579fc6"
    readonly property color activeIndicator: primaryColor
    readonly property color iconDefault: "#b0bfcc"
    readonly property color iconDisabled: "#73808c"
    readonly property color iconHover: "#dce8f1"
    readonly property color iconActive: primaryColor

    // 两侧工具栏使用图标；完整操作名称由悬停和键盘焦点提示提供。
    readonly property int toolbarIconSize: 24
    readonly property int navigationIconSize: 28
    readonly property int toolbarLabelSize: 11
    readonly property int toolbarButtonHeight: 48
    readonly property int controlRadius: 6
    readonly property int bodyFontSize: 13

    readonly property color folderAccent: "#e6bd70"
    readonly property color folderSurface: "#332d23"
    readonly property color fusionAccent: "#77c8bb"
    readonly property int controlHeight: 32
    readonly property int compactControlHeight: 32
    readonly property color inputBorder: "#667888"
    readonly property color sliderTrack: "#667888"

    // Primary command buttons, such as "Open DICOM folder".
    readonly property color primaryButtonBackground: "#21698f"
    readonly property color primaryButtonHover: "#2b82ad"
    readonly property color primaryButtonPressed: "#195574"
    readonly property color primaryButtonDisabled: "#183344"
    readonly property color primaryButtonBorder: "#70c9ef"

    // Semantic status colors. Use their surface variants for backgrounds.
    readonly property color infoColor: primaryColor
    readonly property color infoSurface: "#123247"
    readonly property color successColor: "#7bd7a4"
    readonly property color successSurface: "#17392b"
    readonly property color warningColor: "#f3c66b"
    readonly property color warningSurface: "#3d3119"
    readonly property color dangerColor: "#ef7777"
    readonly property color dangerSurface: "#412124"

    // 重置保留琥珀图标提示；常态使用中性表面，避免抢占影像注意力。
    readonly property color resetActionColor: "#f3c66b"
    readonly property color resetActionSurface: "#302819"
    readonly property color resetActionHover: "#40351e"
    readonly property color resetActionPressed: "#241e14"
    readonly property color resetActionBorder: "#8f7438"

    // Measurement colors are separate from UI selection colors so overlays
    // remain visible on grayscale and pseudo-color images.
    readonly property color measurementPrimary: "#ffd45c"
    readonly property color measurementSelected: "#66d0ff"
    readonly property color measurementHandle: "#f8fbff"

    // Temporary compatibility aliases for existing components.
    readonly property color hoverColor: controlHover
    readonly property color activeColor: selectionBackground
    readonly property color panelColor: panelBackground
    readonly property color textColor: textPrimary
}
