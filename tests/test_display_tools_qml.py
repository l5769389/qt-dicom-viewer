from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, QUrl, Qt
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest
from shiboken6 import delete

from test_measurement_qml import (
    _scene,
    _visual_children,
    qt_app,
    viewport,
)
from test_viewport_transform import _controller, _render_result


def _find(root, name, *, visible=True):
    return next(
        item for item in _visual_children(root)
        if item.objectName() == name
        and (not visible or item.isVisible())
    )


def _click(view, item):
    center = item.mapToScene(
        QPointF(item.width() / 2, item.height() / 2)
    ).toPoint()
    QTest.mouseClick(view, Qt.LeftButton, Qt.NoModifier, center)
    QTest.qWait(50)


@pytest.fixture
def display_panel(qt_app):
    viewport_controller = _controller()
    viewport_controller.handleRenderResult(_render_result(viewport_controller))
    view = QQuickView()
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.resize(330, 720)
    warnings = []
    view.engine().warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    view.setInitialProperties({
        "toolController": viewport_controller._tool_controller,
        "toolVisible": True,
        "viewportController": viewport_controller,
    })
    source = (
        Path(__file__).resolve().parents[1]
        / "src/qt_dicom_viewer/qml/sections/RightPanel.qml"
    )
    view.setSource(QUrl.fromLocalFile(str(source)))
    assert view.status() == QQuickView.Ready, [
        error.toString() for error in view.errors()
    ]
    view.show()
    QTest.qWait(100)
    try:
        yield view, viewport_controller, warnings
    finally:
        view.hide()
        delete(view)


def test_display_tool_panels_change_live_viewport_state(display_panel):
    view, viewport_controller, warnings = display_panel
    root = view.rootObject()

    _click(view, _find(root, "primaryTool-annotate"))
    _find(root, "annotatePanel")
    _find(root, "annotationTextEditor")
    viewport_controller.textAnnotationController.setAnnotationText("病灶")
    viewport_controller.textAnnotationController.addAnnotation(10, 12)
    assert len(viewport_controller.textAnnotationController.annotationItems) == 1

    _click(view, _find(root, "primaryTool-pseudocolor"))
    _find(root, "pseudoColorPanel")
    _click(view, _find(root, "colorMap-blackbody"))
    assert viewport_controller.activeColorMap == "blackbody"

    _click(view, _find(root, "primaryTool-viewport-settings"))
    _find(root, "viewportSettingsPanel")
    scale_setting = _find(root, "viewportSetting-scale-bar")
    _click(view, scale_setting)
    assert viewport_controller.showScaleBar
    assert not warnings, warnings


def test_viewport_renders_text_scale_and_color_overlays(viewport):
    view, controller, pixel_layer, warnings = viewport
    tools = controller._tool_controller
    tools.activateTool("annotate")
    controller.textAnnotationController.setAnnotationText("目标区域")
    controller.textAnnotationController.setAnnotationColor("#66d0ff")
    controller.textAnnotationController.setAnnotationFontSize(22)

    QTest.mouseClick(
        view,
        Qt.LeftButton,
        Qt.NoModifier,
        _scene(pixel_layer, 60, 70),
    )
    QTest.qWait(50)
    item = controller.textAnnotationController.annotationItems[0]
    rendered = _find(view.rootObject(), "textAnnotation-" + item["annotationId"])
    assert rendered.property("width") > 0

    controller.setViewportSetting("scale-bar", True)
    controller.setViewportSetting("color-bar", True)
    QTest.qWait(50)
    assert _find(view.rootObject(), "viewportScaleBar").width() > 0
    assert _find(view.rootObject(), "viewportColorBar").height() > 0

    controller.setViewportSetting("window-annotations", False)
    QTest.qWait(20)
    assert not _find(
        view.rootObject(), "viewportMetadataOverlay", visible=False
    ).isVisible()
    assert not warnings, warnings
