import QtQuick
import QtQuick.Layouts

Image {
    id: imageView
    required property var activeViewport

    source: imageView.activeViewport
        ? imageView.activeViewport.imageSource : ""
    fillMode: Image.PreserveAspectFit
    smooth: true
    cache: false
}