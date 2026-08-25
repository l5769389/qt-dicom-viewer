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
    readonly property color secondarySoft: "#1a2631"

    readonly property color accentWarm: "#ff8a5b"

    // Surface hierarchy. Keep the DICOM canvas darker than application chrome.
    readonly property color appBackground: "#09121a"
    readonly property color shellBackground: "#0b131e"
    readonly property color panelBackground: "#0a121c"
    readonly property color panelBackgroundSoft: "#081019"
    readonly property color panelBackgroundStrong: "#0d1722"
    readonly property color workspaceBackground: "#070d14"
    readonly property color canvasBackground: "#02070e"
    readonly property color cardBackground: "#111c27"
    readonly property color cardBackgroundHover: "#172532"
    readonly property color elevatedBackground: "#182633"

    // Borders and separators.
    readonly property color borderSubtle: "#1c2935"
    readonly property color borderDefault: "#293846"
    readonly property color borderStrong: "#38536a"
    readonly property color dividerColor: "#22303c"
    readonly property color focusBorder: primaryColor

    // Typography.
    readonly property color textPrimary: "#f5f7fb"
    readonly property color textSecondary: "#c5d0da"
    readonly property color textMuted: "#8d9baa"
    readonly property color textSubtle: "#6f7e8d"
    readonly property color textDisabled: "#53616e"
    readonly property color textOnPrimary: "#f8fbff"
    readonly property color overlayText: "#eaf3fb"
    readonly property color overlayOutline: "#cc000000"

    // Generic controls.
    readonly property color controlBackground: "#131e28"
    readonly property color controlHover: "#1b2b38"
    readonly property color controlPressed: "#10202c"
    readonly property color controlDisabled: "#0f171f"
    readonly property color controlBorder: "#263643"
    readonly property color controlHoverBorder: "#3b5b70"

    // Selection / active interaction. A selected item is not a status message.
    readonly property color selectionBackground: "#173449"
    readonly property color selectionHover: "#1d4058"
    readonly property color selectionBorder: "#3f91bd"
    readonly property color activeIndicator: primaryColor
    readonly property color iconDefault: "#96a6b5"
    readonly property color iconHover: "#dce8f1"
    readonly property color iconActive: primaryColor

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
