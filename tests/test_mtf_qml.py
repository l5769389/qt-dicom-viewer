"""真实工具栏、视口鼠标事件和 Canvas 结果的端到端测试。"""

from pathlib import Path
from dataclasses import replace

import numpy as np
import pytest
from PySide6.QtCore import QPointF, Qt, QUrl
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest
from shiboken6 import delete

from qt_dicom_viewer.model import ToolType
from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
from test_measurement_qml import qt_app, _mouse_drag, _scene, _visual_children
from test_mtf_controller import bead_render, wait_result
from test_service_panel_qml import _click, _find
from test_viewport_transform import _controller


@pytest.fixture
def workspace(qt_app, request):
    controller = _controller()
    frame = bead_render(controller)
    controller.handleRenderResult(frame)
    controller._tool_controller.resetRequested.connect(lambda tool: controller.reset_tool_state(ToolType(tool)))
    view = QQuickView()
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    size = getattr(request, "param", (1200, 820))
    view.resize(*size)
    provider = DicomImageProvider()
    provider.set_array(controller.viewport_config.viewport_id, frame.image)
    view.engine().addImageProvider("dicom", provider)
    warnings = []
    view.engine().warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    view.setInitialProperties({"viewportController": controller, "toolController": controller._tool_controller})
    view.setSource(QUrl.fromLocalFile(str(Path(__file__).parent / "qml/MtfWorkspace.qml")))
    assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
    view.show()
    QTest.qWait(80)
    pixels = view.rootObject().findChild(QQuickItem, "dicomPixelLayer")
    try:
        yield view, controller, pixels, warnings
    finally:
        controller.shutdown()
        view.hide()
        delete(view)


@pytest.mark.parametrize("workspace", [(1200, 820), (760, 560)], indirect=True)
def test_real_service_roi_to_canvas_chart_and_metrics(workspace, tmp_path):
    view, controller, pixels, warnings = workspace
    _click(view, _find(view, "primaryTool-service"))
    _click(view, _find(view, "serviceEntry-mtf"))
    assert controller.activeInteraction == "service:mtf"
    _mouse_drag(view, _scene(pixels, 8, 8), _scene(pixels, 118, 118))
    wait_result(controller.mtfController)
    QTest.qWait(100)
    assert controller.mtfController.status == "ready"
    chart = _find(view, "mtfChart")
    assert chart.width() > 200
    legend = _find(view, "mtfThresholdLegend")
    legend_position = legend.mapToItem(chart, QPointF())
    assert legend_position.x() > 0
    assert 0 <= legend_position.y() < 40
    assert legend_position.x() + legend.width() <= chart.width()
    texts = [item.property("text") for item in _visual_children(_find(view, "mtfResults"))
             if item.isVisible() and item.property("text")]
    assert not any("未做微珠尺寸修正" in text for text in texts)
    for index in (1, 2, 3, 5, 6, 7):
        assert float(_find(view, "mtfMetric-" + str(index)).property("text")) > 0
    assert _find(view, "mtfRoiLabel").property("text") == controller.mtfController.roiMetricLabel
    assert controller.mtfController.roiMetricLabel.startswith("ROI  ")
    assert " mm · " in controller.mtfController.roiMetricLabel
    assert " px\n" in controller.mtfController.roiMetricLabel
    badge = _find(view, "mtfRoiMetricBadge")
    badge_top_left = badge.mapToScene(QPointF())
    badge_bottom_right = badge.mapToScene(QPointF(badge.width(), badge.height()))
    assert 0 <= badge_top_left.x() < badge_bottom_right.x() <= view.width()
    assert 0 <= badge_top_left.y() < badge_bottom_right.y() <= view.height()
    assert not [item for item in _visual_children(view.rootObject())
                if item.objectName() == "roiMetricCard" and item.isVisible()]
    status = next(item for item in _visual_children(_find(view, "mtfResults"))
                  if item.objectName() == "mtfStatus")
    assert status.property("text") == "" and not status.isVisible()
    assert not any("质量提示不代表" in text for text in texts)

    measurement_label = _find(view, "mtfMeasurementMethodLabel")
    analysis_label = _find(view, "mtfAnalysisMethodLabel")
    for label, option_names in [
        (measurement_label, ["mtfMeasurementMethod-bead", "mtfMeasurementMethod-wire"]),
        (analysis_label, ["mtfAnalysisMethod-direct_fft", "mtfAnalysisMethod-gaussian"]),
    ]:
        label_center = label.mapToScene(QPointF(0, label.height() / 2)).y()
        assert all(_find(view, name).mapToScene(
            QPointF(0, _find(view, name).height() / 2)).y() == pytest.approx(label_center)
            for name in option_names)

    saved_result = controller.mtfController.currentResult
    x_legend, y_legend = _find(view, "mtfLegend-x"), _find(view, "mtfLegend-y")
    assert chart.property("showX") and chart.property("showY")
    _click(view, x_legend)
    assert not chart.property("showX") and chart.property("showY")
    _click(view, y_legend)
    assert not chart.property("showX") and not chart.property("showY")
    _click(view, x_legend)
    _click(view, y_legend)
    assert chart.property("showX") and chart.property("showY")
    assert controller.mtfController.currentResult == saved_result
    panel = _find(view, "rightPanel")
    results = _find(view, "mtfResults")
    # 水平空间受操作栏约束；高度不足交给外层 Flickable，不挤压或截短指标。
    assert results.width() <= panel.width()
    for item in _visual_children(results):
        if item.isVisible() and item.width() > 0:
            position = item.mapToItem(results, QPointF())
            assert position.x() >= -1
            assert position.x() + item.width() <= results.width() + 1
    screenshot = view.grabWindow()
    assert not screenshot.isNull()
    path = tmp_path / f"mtf-{view.width()}x{view.height()}-dpr{view.devicePixelRatio():g}.png"
    assert screenshot.save(str(path))
    print(f"MTF QML preview: {path}")
    if view.width() < 900:
        flickable = next(item for item in _visual_children(panel)
                         if item.property("contentHeight") is not None
                         and item.property("contentY") is not None
                         and item.property("contentHeight") > item.height())
        flickable.setProperty("contentY", flickable.property("contentHeight") - flickable.height())
        QTest.qWait(50)
        metric = _find(view, "mtfMetric-7")
        metric_y = metric.mapToItem(flickable, QPointF()).y()
        assert 0 <= metric_y <= flickable.height() - metric.height()
        scroll_path = tmp_path / f"mtf-small-scrolled-dpr{view.devicePixelRatio():g}.png"
        assert view.grabWindow().save(str(scroll_path))
        print(f"MTF scrolled preview: {scroll_path}")
        flickable.setProperty("contentY", 0)
        QTest.qWait(20)
    saved = controller.mtfController.roiController.measurementItems
    qa = _find(view, "serviceEntry-qa")
    assert not qa.isEnabled()
    _click(view, qa)
    assert controller.activeInteraction == "service:mtf"
    assert controller._tool_controller.canResetActiveTool
    assert controller.mtfController.roiController.measurementItems == saved
    # 离开 MTF 使用真正可用的平移工具；QA 占位不应切换当前工具。
    _click(view, _find(view, "primaryTool-pan"))
    assert controller.activeInteraction == "pan"
    assert not [item for item in _visual_children(view.rootObject())
                if item.objectName() == "mtfResults" and item.isVisible()]
    _mouse_drag(view, _scene(pixels, 20, 20), _scene(pixels, 90, 90))
    assert controller.mtfController.roiController.measurementItems == saved
    _click(view, _find(view, "primaryTool-service"))
    _click(view, _find(view, "serviceEntry-mtf"))
    assert controller._tool_controller.resetLabel == "重置 MTF"
    controller._tool_controller.resetActiveTool()
    assert controller.mtfController.status == "empty"
    assert not warnings, warnings


def test_canvas_handles_response_above_one_and_missing_crossings(workspace, tmp_path):
    view, controller, pixels, warnings = workspace
    frame = bead_render(controller)
    data = np.zeros((128, 128))
    data[64, 64] = 10
    data[64, 63] = data[64, 65] = -2
    controller.handleRenderResult(replace(frame, modality_pixel=data))
    controller._tool_controller.selectService("service:mtf")
    _mouse_drag(view, _scene(pixels, 20, 20), _scene(pixels, 110, 110))
    wait_result(controller.mtfController)
    QTest.qWait(60)
    assert max(controller.mtfController.currentResult["x"]["mtf"]) > 2
    assert _find(view, "mtfMetric-1").property("text") == "未达到"
    assert _find(view, "mtfMetric-2").property("text") == "未达到"
    assert "MTF50  X 未达到" in _find(view, "mtfRoiLabel").property("text")
    assert view.grabWindow().save(str(tmp_path / "mtf-response-above-one.png"))
    assert not warnings, warnings


def test_method_and_analysis_selectors_apply_simple_roi_rules(workspace):
    view, controller, pixels, warnings = workspace
    _click(view, _find(view, "primaryTool-service"))
    _click(view, _find(view, "serviceEntry-mtf"))
    bead = _find(view, "mtfMeasurementMethod-bead")
    wire = _find(view, "mtfMeasurementMethod-wire")
    direct = _find(view, "mtfAnalysisMethod-direct_fft")
    gaussian = _find(view, "mtfAnalysisMethod-gaussian")
    assert bead.property("selected") and direct.property("selected")
    for label_name, options in [
        ("mtfMeasurementMethodLabel", [bead, wire]),
        ("mtfAnalysisMethodLabel", [direct, gaussian]),
    ]:
        label = _find(view, label_name)
        label_center = label.mapToScene(QPointF(0, label.height() / 2)).y()
        assert all(option.mapToScene(QPointF(0, option.height() / 2)).y()
                   == pytest.approx(label_center) for option in options)

    _mouse_drag(view, _scene(pixels, 8, 8), _scene(pixels, 118, 118))
    wait_result(controller.mtfController)
    roi = controller.mtfController.roiController.measurementItems
    _click(view, gaussian)
    wait_result(controller.mtfController)
    assert controller.mtfController.roiController.measurementItems == roi
    assert controller.mtfController.analysisMethod == "gaussian"
    assert gaussian.property("selected") and not direct.property("selected")

    _click(view, wire)
    assert controller.mtfController.measurementMethod == "wire"
    assert controller.mtfController.status == "empty"
    assert not controller.mtfController.roiController.measurementItems
    assert wire.property("selected") and not bead.property("selected")
    assert "细丝截面" in _find(view, "mtfStatus").property("text")
    assert not warnings, warnings


def test_mtf_metric_badge_moves_roi(workspace):
    view, controller, pixels, warnings = workspace
    controller._tool_controller.selectService("service:mtf")
    _mouse_drag(view, _scene(pixels, 15, 15), _scene(pixels, 105, 105))
    wait_result(controller.mtfController)
    before = controller.mtfController.roiController.measurementItems[0]["points"]
    badge = _find(view, "mtfRoiMetricBadge")
    start = badge.mapToScene(QPointF(badge.width() / 2, badge.height() / 2)).toPoint()
    _mouse_drag(view, start, start + QPointF(12, 8).toPoint())
    wait_result(controller.mtfController)
    after = controller.mtfController.roiController.measurementItems[0]["points"]
    first_delta = (
        after[0]["column"] - before[0]["column"],
        after[0]["row"] - before[0]["row"],
    )
    second_delta = (
        after[1]["column"] - before[1]["column"],
        after[1]["row"] - before[1]["row"],
    )
    assert first_delta == pytest.approx(second_delta)
    assert first_delta != pytest.approx((0, 0))
    assert not warnings, warnings


def test_real_mtf_move_resize_escape_delete_and_transform(workspace):
    view, controller, pixels, warnings = workspace
    controller._tool_controller.selectService("service:mtf")
    _mouse_drag(view, _scene(pixels, 15, 15), _scene(pixels, 105, 105))
    wait_result(controller.mtfController)
    original = controller.mtfController.roiController.measurementItems[0]
    _mouse_drag(view, _scene(pixels, 60, 60), _scene(pixels, 65, 64))
    wait_result(controller.mtfController)
    moved = controller.mtfController.roiController.measurementItems[0]
    assert moved["measurementId"] == original["measurementId"]
    assert moved["points"][0]["column"] == pytest.approx(20, abs=.5)
    controller.applyTransformAction("rotate:cw90")
    controller.applyTransformAction("rotate:mirror-h")
    QTest.qWait(40)
    corner = moved["points"][1]
    _mouse_drag(
        view,
        _scene(pixels, corner["column"], corner["row"]),
        _scene(pixels, corner["column"] + 8, corner["row"] + 8),
    )
    wait_result(controller.mtfController)
    result = controller.mtfController.currentResult
    start = _scene(pixels, 60, 60)
    QTest.mousePress(view, Qt.LeftButton, Qt.NoModifier, start)
    QTest.mouseMove(view, start + QPointF(30, 30).toPoint(), 30)
    QTest.qWait(30)
    assert controller.mtfController.status == "editing"
    assert controller.mtfController.currentResult == {}
    assert not any(item.objectName() == "mtfRoiMetricBadge" and item.isVisible()
                   for item in _visual_children(view.rootObject()))
    QTest.keyClick(view, Qt.Key_Escape)
    QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, start)
    assert controller.mtfController.currentResult == result
    assert _find(view, "mtfRoiMetricBadge").isVisible()
    QTest.keyClick(view, Qt.Key_Backspace)
    assert controller.mtfController.status == "empty"
    assert not controller.mtfController.roiController.measurementItems
    assert not warnings, warnings
