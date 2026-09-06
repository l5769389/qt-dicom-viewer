pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "../components" as Controls

Item {
    id: servicePanel
    objectName: "servicePanel"

    required property var toolController
    property var viewportController: null
    readonly property string selectedService: servicePanel.toolController
        ? servicePanel.toolController.activeService : ""

    signal actionTriggered(string action)

    implicitHeight: content.implicitHeight

    // 内容始终从顶部排列；外层统一负责超出高度后的滚动。
    ColumnLayout {
        id: content
        anchors.top: parent.top
        width: parent.width
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: servicePanel.toolController
                    ? servicePanel.toolController.serviceActions : []

                delegate: Controls.ToolActionButton {
                    id: serviceButton
                    required property var modelData

                    objectName: "serviceEntry-" + serviceButton.modelData.iconName
                    Layout.fillWidth: true
                    Layout.preferredWidth: 1
                    implicitHeight: 44
                    iconSize: 24
                    iconName: serviceButton.modelData.iconName
                    label: serviceButton.modelData.label
                    checked: servicePanel.selectedService === serviceButton.modelData.action
                    enabled: serviceButton.modelData.action !== "service:qa"
                        || !servicePanel.viewportController
                        || !!servicePanel.viewportController.qaController?.available

                    onClicked: servicePanel.actionTriggered(serviceButton.modelData.action)
                }
            }
        }

        MtfResults {
            Layout.fillWidth: true
            visible: servicePanel.selectedService === "service:mtf"
            controller: servicePanel.viewportController?.mtfController ?? null
        }

        WaterQaResults {
            Layout.fillWidth: true
            visible: servicePanel.selectedService === "service:qa"
            controller: servicePanel.viewportController?.qaController ?? null
        }
    }
}
