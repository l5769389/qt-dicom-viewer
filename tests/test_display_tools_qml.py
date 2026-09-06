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

    primary_buttons = [
        item for item in _visual_children(root)
        if item.objectName().startswith("primaryTool-") and item.isVisible()
    ]
    assert primary_buttons
    assert {button.height() for button in primary_buttons} == {48.0}

    _click(view, _find(root, "primaryTool-annotate"))
    _find(root, "annotatePanel")
    _find(root, "annotationTextEditor")
    viewport_controller.textAnnotationController.setAnnotationText("病灶")
    viewport_controller.textAnnotationController.addAnnotation(10, 12, 48, 34)
    assert len(viewport_controller.textAnnotationController.annotationItems) == 1

    _click(view, _find(root, "primaryTool-pseudocolor"))
    _find(root, "pseudoColorPanel")
    _click(view, _find(root, "colorMap-blackbody"))
    assert viewport_controller.activeColorMap == "blackbody"

    _click(view, _find(root, "primaryTool-viewport-settings"))
    _find(root, "viewportSettingsPanel")
    scale_setting = _find(root, "viewportSetting-scale-bar")
    _click(view, scale_setting)
    assert not viewport_controller.showScaleBar
    assert not warnings, warnings


def test_viewport_drag_renders_arrow_label_scale_and_color_overlays(
        viewport,
        tmp_path,
):
    view, controller, pixel_layer, warnings = viewport
    tools = controller._tool_controller
    tools.activateTool("annotate")
    controller.setAnnotationMode(True)
    controller.textAnnotationController.setAnnotationText("目标区域")
    controller.textAnnotationController.setAnnotationColor("#66d0ff")
    controller.textAnnotationController.setAnnotationFontSize(22)

    start = _scene(pixel_layer, 60, 70)
    end = _scene(pixel_layer, 135, 35)
    QTest.mousePress(view, Qt.LeftButton, Qt.NoModifier, start)
    QTest.mouseMove(view, (start + end) / 2, 20)
    QTest.qWait(20)
    draft_item = controller.textAnnotationController.annotationItems[0]
    assert draft_item["draft"]
    draft_arrow = _find(
        view.rootObject(),
        "annotationArrow-" + draft_item["annotationId"],
    )
    assert draft_arrow.property("draftStyle")

    QTest.mouseMove(view, end, 20)
    QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, end)
    QTest.qWait(40)
    item = controller.textAnnotationController.annotationItems[0]
    assert not item["draft"]
    assert item["tailColumn"] == pytest.approx(60, abs=1)
    assert item["tailRow"] == pytest.approx(70, abs=1)
    assert item["headColumn"] == pytest.approx(135, abs=1)
    assert item["headRow"] == pytest.approx(35, abs=1)
    rendered = _find(view.rootObject(), "textAnnotation-" + item["annotationId"])
    arrow = _find(view.rootObject(), "annotationArrow-" + item["annotationId"])
    label = _find(view.rootObject(), "annotationLabel-" + item["annotationId"])
    assert rendered.property("arrowLength") > 20
    assert arrow.isVisible()
    assert not arrow.property("draftStyle")
    assert label.width() > 0

    controller.textAnnotationController.clearSelection()
    QTest.mouseClick(
        view,
        Qt.LeftButton,
        Qt.NoModifier,
        _scene(pixel_layer, 98, 52),
    )
    QTest.qWait(20)
    assert controller.textAnnotationController.selectedAnnotationId \
        == item["annotationId"]
    assert len(controller.textAnnotationController.annotationItems) == 1

    controller.setViewportSetting("scale-bar", True)
    controller.setViewportSetting("color-bar", True)
    QTest.qWait(50)
    assert _find(view.rootObject(), "imageScaleBar").width() > 0
    assert _find(view.rootObject(), "viewportColorBar").height() > 0

    controller.setViewportSetting("window-annotations", False)
    QTest.qWait(20)
    assert not _find(
        view.rootObject(), "viewportMetadataOverlay", visible=False
    ).isVisible()
    screenshot = view.grabWindow()
    if not screenshot.isNull():
        output = tmp_path / "arrow-annotation.png"
        assert screenshot.save(str(output))
        print(f"QML preview: {output}")
    assert not warnings, warnings
