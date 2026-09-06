import QtQuick
import QtQuick.Shapes

Item {
    id: icon
    property color tint: "#b0bfcc"
    Item {
        width: 24; height: 24
        transform: Scale { xScale: icon.width / 24; yScale: icon.height / 24 }
        // A grayscale ramp maps to a color ramp. Keep the bands legible at 24 px.
        Rectangle {
            x: 2; y: 3; width: 6; height: 18; radius: 1
            border.width: 0.6; border.color: icon.tint
            gradient: Gradient {
                GradientStop { position: 0; color: "#eef4f8" }
                GradientStop { position: 1; color: "#35424e" }
            }
        }
        Rectangle {
            x: 16; y: 3; width: 6; height: 18; radius: 1
            gradient: Gradient {
                GradientStop { position: 0; color: "#df856f" }
                GradientStop { position: 0.2; color: "#e6cd77" }
                GradientStop { position: 0.4; color: "#8cd594" }
                GradientStop { position: 0.7; color: "#4ac9ce" }
                GradientStop { position: 1; color: "#617edb" }
            }
        }
        Shape {
            anchors.fill: parent
            ShapePath {
                strokeColor: icon.tint; strokeWidth: 1.3; fillColor: "transparent"
                capStyle: ShapePath.RoundCap; joinStyle: ShapePath.RoundJoin
                PathSvg { path: "M10,12H13.5M11.5,9.5L14,12L11.5,14.5" }
            }
        }
    }
}
