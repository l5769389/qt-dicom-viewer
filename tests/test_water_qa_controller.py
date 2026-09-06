from dataclasses import replace
from threading import Event
import time

import numpy as np
import pytest
from PySide6.QtCore import QThread

from qt_dicom_viewer.core.water_qa import analyze_water_phantom
from qt_dicom_viewer.model import PixelSpacing, ToolType, WindowLevel
from qt_dicom_viewer.ui.controller.viewport.controller.water_qa_controller import WaterQaController
from test_measurement_qml import qt_app
from test_viewport_transform import _controller, _render_result
from test_water_qa import water_image


def water_render(view, index=0, spacing=(1, 1), pixels=None):
    base = _render_result(view)
    pixels = water_image(mean=2+index*3) if pixels is None else pixels
    rows, columns = pixels.shape
    meta = replace(base.frame_meta, slice_index=index, slice_count=4,
                   geometry=replace(base.frame_meta.geometry, rows=rows, columns=columns,
                                    pixel_spacing=PixelSpacing(*spacing)),
                   instance_meta=replace(base.frame_meta.instance_meta, rows=rows, columns=columns,
                                         pixel_spacing=spacing, sop_instance_uid=f"water-{index}"))
    return replace(base, series_uid=view.viewport_config.series_uid, frame_meta=meta,
                   modality_pixel=pixels, image=np.clip((pixels+150)*255/300, 0, 255).astype(np.uint8))


@pytest.fixture
def qa_view(qt_app):
    view = _controller()
    frame = water_render(view)
    view.handleRenderResult(frame)
    try:
        yield view, frame
    finally:
        view.shutdown()


def pump_until(app, condition):
    deadline = time.monotonic()+5
    while not condition() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.005)
    app.processEvents()
    assert condition(), "后台 QA 未及时完成"


def wait_qa(app, controller):
    pump_until(app, lambda: controller.status != "calculating")
    assert controller.status == "ready", controller.error


def finish(qa, job):
    token, key, pixels, spacing, settings = job
    result = analyze_water_phantom(pixels, spacing, settings)
    qa._receive_result(token, key, result, "")
    return result


def test_service_activation_runs_worker_and_returns_five_rois_on_gui_thread(qa_view, qt_app):
    view, _ = qa_view
    qa, tools = view.qaController, view._tool_controller
    threads = []
    qa.stateChanged.connect(lambda: threads.append(QThread.currentThread()))
    assert qa.status == "empty" and not qa.enabled
    tools.selectService("service:qa")
    wait_qa(qt_app, qa)
    assert qa.enabled and len(qa.roiItems) == 5
    assert qa.currentResult["noise_hu"] == pytest.approx(5, abs=1)
    assert tools.activeInteraction == ""
    assert tools.resetLabel == "重置水模 QA"
    assert view.measurementController.measurementItems == []
    assert view.mtfController.roiController.measurementItems == []
    assert all(thread == view.thread() for thread in threads)
    assert not {"passed", "failed", "grade", "tolerance"} & qa.currentResult.keys()


def test_display_changes_reuse_result_and_resets_are_scoped(qa_view, qt_app):
    view, frame = qa_view
    tools, qa = view._tool_controller, view.qaController
    tools.resetRequested.connect(lambda tool: view.reset_tool_state(ToolType(tool)))
    tools.selectService("service:qa")
    wait_qa(qt_app, qa)
    original = qa.currentResult
    token = qa._token
    tools.activateTool("pan")
    view.apply_pan(20, -30)
    view.apply_zoom(1.4)
    view.applyTransformAction("rotate:cw90")
    view.applyTransformAction("rotate:mirror-h")
    view.handleRenderResult(replace(frame, image=255-frame.image,
        frame_meta=replace(frame.frame_meta, window=WindowLevel(100, 500), inverted=True)))
    assert qa.currentResult == original and qa._token == token
    view.reset_tool_state(ToolType.MEASURE)
    assert qa.currentResult == original
    tools.activateTool("service")
    tools.resetActiveTool()
    assert not qa.enabled and qa.currentResult == {} and not qa.roiItems
    assert qa.roiDiameterMm == qa.edgeClearanceMm == 20
    tools.selectService("service:qa")  # Reselecting the same service restarts after reset.
    wait_qa(qt_app, qa)
    view.reset_all_view_state()
    assert not qa.enabled and qa.currentResult == {}


def test_auto_activation_before_load_and_missing_pixel_spacing(qt_app):
    view = _controller()
    try:
        tools, qa = view._tool_controller, view.qaController
        tools.selectService("service:qa")
        assert qa.status == "waiting"
        frame = water_render(view)
        view.handleRenderResult(frame)
        wait_qa(qt_app, qa)
        missing = replace(frame, frame_meta=replace(frame.frame_meta,
            instance_meta=replace(frame.frame_meta.instance_meta, pixel_spacing=None)))
        view.handleRenderResult(missing)
        pump_until(qt_app, lambda: qa.status != "calculating")
        assert qa.status == "error" and "PixelSpacing" in qa.error
        assert qa.currentResult == {} and not qa.roiItems
    finally:
        view.shutdown()


def test_parameter_edits_discard_old_results_and_update_geometry(qa_view, qt_app):
    view, _ = qa_view
    qa = view.qaController
    qa.activate()
    wait_qa(qt_app, qa)
    previous = qa.currentResult
    qa.setRoiDiameterMm(30)
    assert qa.currentResult == {} and not qa.roiItems
    wait_qa(qt_app, qa)
    assert qa.currentResult["rois"][0]["area_mm2"] > previous["rois"][0]["area_mm2"]
    qa.setEdgeClearanceMm(10)
    wait_qa(qt_app, qa)
    assert qa.currentResult["settings"]["edge_clearance_mm"] == 10
    qa.setRoiDiameterMm(100)
    pump_until(qt_app, lambda: qa.status != "calculating")
    assert qa.status == "error" and qa.roiItems == []
    assert "互不重叠" in qa.error
    qa.setRoiDiameterMm(20)
    wait_qa(qt_app, qa)


def test_slice_cache_stale_callbacks_reset_and_changed_raw_pixels(qa_view, monkeypatch):
    view, first = qa_view
    qa = view.qaController
    jobs = []
    monkeypatch.setattr(qa, "_submit", lambda *args: jobs.append(args))
    qa.activate()
    old = jobs[-1]
    view.apply_slice_index(1)
    assert not qa.roiItems and qa.currentResult == {} and qa.status == "waiting"
    second = water_render(view, 1)
    view.handleRenderResult(second)
    latest = jobs[-1]
    finish(qa, old)
    assert qa.status == "calculating" and not qa.currentResult
    finish(qa, latest)
    result_second = qa.currentResult
    view.apply_slice_index(0)
    view.handleRenderResult(first)
    finish(qa, jobs[-1])
    count = len(jobs)
    view.apply_slice_index(1)
    view.handleRenderResult(second)
    assert len(jobs) == count and qa.currentResult == result_second
    modified = replace(second, modality_pixel=second.modality_pixel+1)
    view.handleRenderResult(modified)
    assert len(jobs) == count+1
    latest = jobs[-1]
    qa.reset()
    finish(qa, latest)
    assert not qa.enabled and not qa.currentResult


def test_fast_slice_changes_coalesce_to_latest_snapshot(qa_view, qt_app, monkeypatch):
    view, _ = qa_view
    qa = view.qaController
    entered, release = Event(), Event()
    calls = []
    def delayed(pixels, spacing, settings):
        calls.append(float(np.median(pixels[100:180, 180:230])))
        if len(calls) == 1:
            entered.set()
            assert release.wait(5)
        return analyze_water_phantom(pixels, spacing, settings)
    monkeypatch.setattr("qt_dicom_viewer.ui.controller.viewport.controller.water_qa_controller.analyze_water_phantom", delayed)
    qa.activate()
    pump_until(qt_app, entered.is_set)
    try:
        for index in (1, 2, 3):
            view.apply_slice_index(index)
            view.handleRenderResult(water_render(view, index))
            assert len(qa._tasks) == 1 and qa._pending is not None
    finally:
        release.set()
    wait_qa(qt_app, qa)
    assert len(calls) == 2
    assert qa.currentResult["water_ct_hu"] == pytest.approx(11, abs=1)


def test_snapshots_independent_viewports_and_shutdown_ignore_callbacks(qa_view, monkeypatch):
    view, frame = qa_view
    qa = view.qaController
    jobs = []
    monkeypatch.setattr(qa, "_submit", lambda *args: jobs.append(args))
    qa.activate()
    job = jobs[-1]
    frame.modality_pixel[:] = -1000
    result = finish(qa, job)
    assert result.water_ct_hu == pytest.approx(2, abs=1)
    other = _controller()
    try:
        assert not other.qaController.enabled and not other.qaController.currentResult
        qa.shutdown()
        qa._receive_result(job[0], job[1], result, "")
        qa.activate()
        assert not qa.enabled and not qa.currentResult
    finally:
        other.shutdown()
    mr = WaterQaController("MR")
    mr.activate()
    assert not mr.available and not mr.enabled
    mr.shutdown()
