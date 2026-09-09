import QtQuick
import QtQuick.Window

Image {
    property color tint: "#b0bfcc"
    source: "image://navigation/pseudocolor/" + encodeURIComponent(tint.toString())
    sourceSize.width: Math.ceil(width * Math.max(1, Screen.devicePixelRatio))
    sourceSize.height: Math.ceil(height * Math.max(1, Screen.devicePixelRatio))
    smooth: true
    mipmap: true
}
