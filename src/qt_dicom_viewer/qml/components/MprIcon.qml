import QtQuick
import QtQuick.Shapes

Item {
    id: icon
    property color tint: "#b0bfcc"
    // Three separated planes; the silhouette intentionally has no common cube rim.
    Shape {
        width: 24; height: 24
        transform: Scale { xScale: icon.width / 24; yScale: icon.height / 24 }
        ShapePath {
            strokeWidth: 1.5; strokeColor: icon.tint
            fillColor: Qt.rgba(icon.tint.r, icon.tint.g, icon.tint.b, 0.16)
            joinStyle: ShapePath.MiterJoin
            PathSvg { path: "M2.5,2.5H12.5V12.5H2.5Z" }
        }
        ShapePath {
            strokeWidth: 1.5; strokeColor: icon.tint
            fillColor: Qt.rgba(icon.tint.r, icon.tint.g, icon.tint.b, 0.30)
            joinStyle: ShapePath.MiterJoin
            PathSvg { path: "M17,3.5L21.5,7.5V17.5L17,13.5Z" }
        }
        ShapePath {
            strokeWidth: 1.5; strokeColor: icon.tint
            fillColor: Qt.rgba(icon.tint.r, icon.tint.g, icon.tint.b, 0.48)
            joinStyle: ShapePath.MiterJoin
            PathSvg { path: "M7,16H14L9.5,21.5H2.5Z" }
        }
    }
}
