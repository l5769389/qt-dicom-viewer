import QtQuick
import QtQuick.Shapes

Item {
    id: icon
    property color tint: "#b0bfcc"
    // MPR's shared reference point, framed by the corners of an image plane.
    Shape {
        width: 24; height: 24
        transform: Scale { xScale: icon.width / 24; yScale: icon.height / 24 }
        ShapePath {
            strokeColor: icon.tint; strokeWidth: 1.4
            fillColor: "transparent"; capStyle: ShapePath.SquareCap
            PathSvg { path: "M8,3H3V8M16,3H21V8M21,16V21H16M8,21H3V16" }
        }
        ShapePath {
            strokeColor: icon.tint; strokeWidth: 1.7
            fillColor: "transparent"; capStyle: ShapePath.RoundCap
            PathSvg { path: "M12,2V8M12,16V22M2,12H8M16,12H22" }
        }
    }
    Rectangle {
        anchors.centerIn: parent
        width: icon.width * 3 / 24; height: width; radius: width / 2
        color: icon.tint
    }
}
