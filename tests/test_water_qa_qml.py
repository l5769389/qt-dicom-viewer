from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QPointF, Qt, QUrl
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest
from shiboken6 import delete

from qt_dicom_viewer.model import ToolType
from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
from test_measurement_qml import qt_app, _visual_children
from test_service_panel_qml import _find, _click
from test_water_qa import water_image
from test_water_qa_controller import qa_view, water_render, wait_qa


@pytest.fixture
def qa_workspace(qt_app, qa_view, request):
    controller, _ = qa_view
    pixels = water_image(shape=(400, 512), spacing=(.7, .5), center=(265, 196))
    frame = water_render(controller, spacing=(.7, .5), pixels=pixels)
    controller.handleRenderResult(frame)
    controller._tool_controller.resetRequested.connect(lambda tool: controller.reset_tool_state(ToolType(tool)))
    window = QQuickView()
    window.setResizeMode(QQuickView.SizeRootObjectToView)
    window.resize(*getattr(request, "param", (1200, 820)))
    provider = DicomImageProvider()
    provider.set_array(controller.viewport_config.viewport_id, frame.image)
    window.engine().addImageProvider("dicom", provider)
    warnings = []
    window.engine().warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    window.setInitialProperties(dict(viewportController=controller, toolController=controller._tool_controller))
    window.setSource(QUrl.fromLocalFile(str(Path(__file__).parent/"qml/MtfWorkspace.qml")))
    assert window.status() == QQuickView.Ready, [e.toString() for e in window.errors()]
    window.show()
    QTest.qWait(70)
    try:
        yield window, controller, warnings
    finally:
        window.hide()
        delete(window)


@pytest.mark.parametrize("qa_workspace", [(1200, 820), (760, 560)], indirect=True)
def test_actual_qa_button_draws_five_rois_and_measures_current_slice(qa_workspace, qt_app, tmp_path):
    window, view, warnings = qa_workspace
    _click(window, _find(window, "primaryTool-service"))
    _click(window, _find(window, "serviceEntry-qa"))
    wait_qa(qt_app, view.qaController)
    QTest.qWait(40)
    rois = [item for item in _visual_children(window.rootObject())
            if item.objectName().startswith("waterQaVoi-")]
    assert len(rois) == 5
    assert all(roi.isVisible() for roi in rois)
    result = view.qaController.currentResult
    for key in ("water_ct_hu", "noise_hu", "uniformity_hu", "consistency_range_hu",
                "horizontal_difference_hu", "vertical_difference_hu"):
        item = _find(window, "waterQaMetric-"+key)
        assert item.property("text") == f"{result[key]:.2f} HU"
    assert len([item for item in _visual_children(window.rootObject())
                if item.objectName().startswith("waterQaRow-") and item.isVisible()]) == 5
    assert "中心" in _find(window, "waterQaVoiLabel-center").property("text")
    texts = [item.property("text") for item in _visual_children(window.rootObject()) if item.isVisible()]
    assert not any(text in ("通过", "不通过", "合格", "不合格") for text in texts)
    image = window.grabWindow()
    assert image.save(str(tmp_path/f"water-qa-{window.width()}x{window.height()}.png"))
    if window.width() < 900:
        flick = _find(window, "toolDetailFlickable")
        assert flick.property("contentHeight") > flick.height()
        flick.setProperty("contentY", flick.property("contentHeight")-flick.height())
        QTest.qWait(20)
        last = _find(window, "waterQaRow-bottom")
        local = last.mapToItem(flick, QPointF()).y()
        assert 0 <= local and local+last.height() <= flick.height()
    assert not warnings, warnings


def test_overlay_tracks_physical_transform_and_parameter_reset(qa_workspace, qt_app):
    window, view, warnings = qa_workspace
    tools = view._tool_controller
    tools.selectService("service:qa")
    wait_qa(qt_app, view.qaController)
    QTest.qWait(30)
    result = view.qaController.currentResult
    pixel_layer = _find(window, "dicomPixelLayer")
    for action in (lambda: None, lambda: view.apply_pan(21, -17), lambda: view.apply_zoom(1.3),
                   lambda: view.applyTransformAction("rotate:cw90"),
                   lambda: view.applyTransformAction("rotate:mirror-h"),
                   lambda: view.applyTransformAction("rotate:mirror-v")):
        action()
        QTest.qWait(20)
        for roi in view.qaController.roiItems:
            item = _find(window, "waterQaVoi-"+roi["key"])
            expected = pixel_layer.mapToItem(item, QPointF(roi["column"]+.5, roi["row"]+.5))
            point = item.property("center")
            assert point.x() == pytest.approx(expected.x(), abs=.01)
            assert point.y() == pytest.approx(expected.y(), abs=.01)
            u, v = item.property("u"), item.property("v")
            rx, ry = np.hypot(u.x()-point.x(), u.y()-point.y()), np.hypot(v.x()-point.x(), v.y()-point.y())
            assert rx == pytest.approx(ry, abs=.01)
        assert view.qaController.currentResult == result
    number = _find(window, "waterQaSetting-roiDiameterMm")
    _click(window, number)
    QTest.keyClick(window, Qt.Key_Up)
    wait_qa(qt_app, view.qaController)
    assert view.qaController.roiDiameterMm == 21
    _click(window, _find(window, "activeToolReset"))
    assert view.qaController.roiItems == [] and not view.qaController.enabled
    _click(window, _find(window, "waterQa-analyze"))
    wait_qa(qt_app, view.qaController)
    assert len(view.qaController.roiItems) == 5
    assert not warnings, warnings
