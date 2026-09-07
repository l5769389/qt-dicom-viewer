pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Shapes

// Cursor-only vectors: no asynchronous raster loading or opaque tool badge.
Item {
    id: glyph
    required property string iconName
    readonly property var paths: ({
        window: "M12 3 A9 9 0 1 0 12 21 A9 9 0 1 0 12 3 M12 3 V21 M12 3 A9 9 0 0 1 12 21 Z",
        zoom: "M10 3 A7 7 0 1 0 10 17 A7 7 0 1 0 10 3 M15 15 L22 22 M6 10 H14 M10 6 V14",
        scroll: "M7 3 V20 M3 7 L7 3 L11 7 M17 4 V21 M13 17 L17 21 L21 17",
        pan: "M12 2 V22 M2 12 H22 M8 6 L12 2 L16 6 M8 18 L12 22 L16 18 M6 8 L2 12 L6 16 M18 8 L22 12 L18 16",
        "crosshair-move": "M12 1 V7 M12 17 V23 M1 12 H7 M17 12 H23 M12 8 A4 4 0 1 0 12 16 A4 4 0 1 0 12 8",
        "crosshair-rotate": "M5 7 A8 8 0 0 1 20 12 M5 2 V7 H10 M19 17 A8 8 0 0 1 4 12 M19 22 V17 H14 M12 8 V16 M8 12 H16",
        "rotate-3d": "M4 8 L12 4 L20 8 L12 12 Z M4 8 V16 L12 20 L20 16 V8 M12 12 V20 M2 5 A12 8 0 0 1 22 5 M19 2 L22 5 L19 7",
        voi: "M12 3 A9 9 0 1 0 12 21 A9 9 0 1 0 12 3 M12 9 V15 M9 12 H15",
        segmentation: "M3 3 H21 V21 H3 Z M7 7 H10 M14 7 H17 M7 12 H10 M14 12 H17 M7 17 H10",
        resize: "M3 9 V3 H9 M3 3 L21 21 M15 21 H21 V15",
        mtf: "M3 3 V21 H21 M6 16 L10 8 L14 16 L18 8 L22 16"
    })
    readonly property string pathData: paths[iconName] || ""
    Shape {
        width: 24; height: 24
        antialiasing: true
        transform: Scale { xScale: glyph.width / 24; yScale: glyph.height / 24 }
        ShapePath {
            strokeColor: "transparent"
            fillColor: glyph.iconName === "window" ? "#ffffff" : "transparent"
            PathSvg { path: "M12 4 A8 8 0 0 0 12 20 Z" }
        }
        ShapePath {
            strokeColor: "#101820"; strokeWidth: 4
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap; joinStyle: ShapePath.RoundJoin
            PathSvg { path: glyph.pathData }
        }
        ShapePath {
            strokeColor: "#ffffff"; strokeWidth: 1.8
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap; joinStyle: ShapePath.RoundJoin
            PathSvg { path: glyph.pathData }
        }
    }
}
