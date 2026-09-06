"""验证提交边界、切片缓存及乱序任务，显示变换不属于重算条件。"""

from dataclasses import replace
from threading import Event

import numpy as np
import pytest
from PySide6.QtCore import QPointF, QThread
from PySide6.QtTest import QTest

from qt_dicom_viewer.core.bead_mtf import compute_point_source_mtf
from qt_dicom_viewer.model import PixelSpacing, TabType, ToolType, WindowLevel
from qt_dicom_viewer.ui.controller.tab.tool_controller import ToolController
from test_bead_mtf import gaussian
from test_measurement_qml import qt_app
from test_viewport_transform import _controller, _render_result


def deliver_frame(view, frame):
    # These fixtures emulate a newly completed render of the requested slice.
    # QA/MTF task staleness is tested independently of renderer request IDs.
    view.handleRenderResult(replace(frame, response_id=view._latest_request_id or frame.response_id))


def bead_render(viewport):
    base = _render_result(viewport)
    pixels = gaussian()
    return replace(base, modality_pixel=pixels, image=np.clip(pixels / 5, 0, 255).astype(np.uint8),
                   frame_meta=replace(base.frame_meta, slice_count=3,
                       geometry=replace(base.frame_meta.geometry, rows=128, columns=128,
                                        pixel_spacing=PixelSpacing(.15, .1)),
                       instance_meta=replace(base.frame_meta.instance_meta, rows=128, columns=128,
                                             pixel_spacing=(.15, .1))))


@pytest.fixture
def mtf_viewport(qt_app):
    view = _controller()
    frame = bead_render(view)
    deliver_frame(view, frame)
    view._tool_controller.selectService("service:mtf")
    try:
        yield view, frame
    finally:
        view.shutdown()


def draw(view, start=(8, 8), end=(118, 118)):
    view.beginInteraction(0, 0, 1, True, *start, .1, .1)
    view.endInteraction(50, 50, True, *end)


def wait_result(controller):
    # 首次在后台线程初始化 NumPy FFT 可能明显慢于后续任务。
    for _ in range(500):
        if controller.status != "calculating":
            return
        QTest.qWait(10)
    pytest.fail("后台 MTF 未在超时内完成")


def capture_tasks(view, monkeypatch):
    jobs = []
    monkeypatch.setattr(view.mtfController, "_submit", lambda *args: jobs.append(args))
    return jobs


def finish(view, job):
    token, pixels, spacing = job
    result = compute_point_source_mtf(
        pixels,
        *spacing,
        measurement_method=token.measurement_method,
        analysis_method=token.analysis_method,
    )
    view.mtfController._receive_result(token, result, "")
    return result


def test_real_thread_result_and_independent_measurements(mtf_viewport):
    view, _ = mtf_viewport
    callback_threads = []
    view.mtfController.stateChanged.connect(lambda: callback_threads.append(QThread.currentThread()))
    draw(view, (118, 118), (8, 8))
    wait_result(view.mtfController)
    assert view.mtfController.status == "ready"
    assert view.mtfController.currentResult["x"]["mtf50"] > 0
    assert view.measurementController.measurementItems == []
    roi = view.mtfController.roiController.measurementItems
    assert len(roi) == 1 and roi[0]["metrics"]["pixel_count"] == 0
    view._tool_controller.selectInteraction("measure:rect")
    draw(view)
    assert len(view.measurementController.measurementItems) == 1
    view.reset_tool_state(ToolType.MEASURE)
    assert view.measurementController.measurementItems == []
    assert view.mtfController.roiController.measurementItems == roi
    assert all(thread == view.thread() for thread in callback_threads)


def test_method_defaults_switching_and_analysis_recalculation(mtf_viewport, monkeypatch):
    view, _ = mtf_viewport
    controller = view.mtfController
    jobs = capture_tasks(view, monkeypatch)
    assert controller.measurementMethod == "bead"
    assert controller.analysisMethod == "direct_fft"

    draw(view)
    finish(view, jobs[-1])
    roi = controller.roiController.measurementItems
    direct_value = controller.currentResult["x"]["mtf50"]

    controller.setAnalysisMethod("gaussian")
    assert controller.analysisMethod == "gaussian"
    assert controller.roiController.measurementItems == roi
    assert controller.status == "calculating"
    assert jobs[-1][0].analysis_method == "gaussian"
    finish(view, jobs[-1])
    assert controller.analysisMethod == "gaussian"
    assert controller.currentResult["x"]["mtf50"] != direct_value
    assert controller.statusText == ""
    assert controller.roiMetricLabel == (
        "ROI  11.00 × 11.00 mm · 111 × 74 px\n"
        f"MTF50  X {controller.currentResult['x']['mtf50']:.3f} · "
        f"Y {controller.currentResult['y']['mtf50']:.3f} lp/mm\n"
        f"MTF10  X {controller.currentResult['x']['mtf10']:.3f} · "
        f"Y {controller.currentResult['y']['mtf10']:.3f} lp/mm"
    )

    controller.setMeasurementMethod("wire")
    assert controller.measurementMethod == "wire"
    assert controller.status == "empty"
    assert not controller.roiController.measurementItems
    assert controller.currentResult == {}
    assert controller.roiMetricLabel == ""
    assert "细丝截面" in controller.statusText

    draw(view)
    assert jobs[-1][0].measurement_method == "wire"
    assert jobs[-1][0].analysis_method == "gaussian"
    finish(view, jobs[-1])
    assert controller.measurementMethod == "wire"


def test_only_commit_submits_and_display_operations_do_not_recompute(mtf_viewport, monkeypatch):
    view, frame = mtf_viewport
    jobs = capture_tasks(view, monkeypatch)
    view.beginInteraction(0, 0, 1, True, 8, 8, .1, .1)
    view.updateInteraction(QPointF(), QPointF(50, 50), QPointF(50, 50), QPointF(50, 50), True, 118, 118)
    assert view.mtfController.status == "editing"
    assert view.mtfController.currentResult == {}
    assert not jobs
    view.endInteraction(50, 50, True, 118, 118)
    assert len(jobs) == 1
    finish(view, jobs[0])
    saved = view.mtfController.currentResult
    view.applyTransformAction("rotate:cw90")
    view.applyTransformAction("rotate:mirror-h")
    view.apply_zoom(2)
    view._tool_controller.activateTool("pan")
    view.beginInteraction(0, 0, 1, True, 30, 30, .1, .1)
    view.updateInteraction(QPointF(), QPointF(10, 10), QPointF(10, 10), QPointF(10, 10), True, 40, 40)
    view.endInteraction(10, 10, True, 40, 40)
    deliver_frame(view, replace(frame, frame_meta=replace(frame.frame_meta, window=WindowLevel(100, 1000))))
    view.updateCursorPosition(10, 10, 20, 20, 20, 20, True, .1, .1)
    assert len(jobs) == 1
    assert view.mtfController.currentResult == saved
    view.deleteSelectedMeasurement()  # 非 MTF 模式不能删除 MTF ROI。
    assert len(view.mtfController.roiController.measurementItems) == 1


def test_mtf_roi_draw_and_corner_resize_stay_physically_square(mtf_viewport, monkeypatch):
    view, _ = mtf_viewport
    capture_tasks(view, monkeypatch)

    draw(view, (20, 30), (70, 50))
    roi = view.mtfController.roiController.measurementItems[0]
    assert roi["metrics"]["width_mm"] == pytest.approx(3)
    assert roi["metrics"]["height_mm"] == pytest.approx(3)
    assert roi["points"][1]["column"] == pytest.approx(20 + 3 / .1)

    # 右下角向非正方形方向拖动，编辑后仍保持物理宽高相等。
    corner = roi["points"][1]
    draw(view, (corner["column"], corner["row"]), (90, 55))
    resized = view.mtfController.roiController.measurementItems[0]
    assert resized["metrics"]["width_mm"] == pytest.approx(
        resized["metrics"]["height_mm"]
    )

    # 普通矩形仍按自由宽高绘制。
    view._tool_controller.selectInteraction("measure:rect")
    draw(view, (20, 30), (70, 50))
    ordinary = view.measurementController.measurementItems[0]
    assert ordinary["metrics"]["width_mm"] == pytest.approx(5)
    assert ordinary["metrics"]["height_mm"] == pytest.approx(3)


def test_move_resize_cancel_replace_and_stale_versions(mtf_viewport, monkeypatch):
    view, _ = mtf_viewport
    jobs = capture_tasks(view, monkeypatch)
    draw(view, (10, 10), (95, 95))
    finish(view, jobs[0])
    initial = view.mtfController.currentResult
    roi = view.mtfController.roiController
    first_id = roi.measurementItems[0]["measurementId"]
    view.beginInteraction(0, 0, 1, True, 50, 50, .1, .1)
    assert view.mtfController.status == "editing" and view.mtfController.currentResult == {}
    view.cancelMeasurement()
    assert view.mtfController.currentResult == initial
    draw(view, (50, 50), (55, 56))  # 内部整体移动。
    moved = roi.measurementItems[0]
    assert moved["points"] == [
        {"column": 15, "row": 16},
        {"column": 100, "row": pytest.approx(72.6666667)},
    ]
    corner = moved["points"][1]
    draw(view, (corner["column"], corner["row"]), (116, 118))  # 调整角点。
    assert roi.measurementItems[0]["measurementId"] == first_id
    newest = finish(view, jobs[2])
    finish(view, jobs[1])  # 旧移动请求不得覆盖新的缩放结果。
    assert view.mtfController.currentResult["x"]["mtf50"] == newest.x.mtf50
    view.beginInteraction(0, 0, 1, True, 2, 2, .1, .1)
    view.cancelMeasurement()
    assert roi.measurementItems[0]["measurementId"] == first_id
    draw(view, (2, 2), (124, 124))
    assert len(roi.measurementItems) == 1
    assert roi.measurementItems[0]["measurementId"] != first_id
    finish(view, jobs[0])
    assert view.mtfController.status == "calculating"


def test_slice_geometry_and_instance_isolation_and_restore(mtf_viewport, monkeypatch):
    view, frame = mtf_viewport
    jobs = capture_tasks(view, monkeypatch)
    draw(view)
    first_roi = view.mtfController.roiController.measurementItems
    view.apply_slice_index(1)
    assert view.mtfController.status == "empty"
    assert not view.mtfController.roiController.measurementItems
    finish(view, jobs[0])
    assert view.mtfController.currentResult == {}
    other = replace(frame, frame_meta=replace(frame.frame_meta, slice_index=1))
    deliver_frame(view, other)
    draw(view)
    finish(view, jobs[1])
    assert len(view.mtfController.roiController.committed_measurements) == 2
    deliver_frame(view, frame)
    assert view.mtfController.roiController.measurementItems == first_roi
    assert view.mtfController.status == "ready"
    for changed in [replace(frame.frame_meta, instance_meta=replace(frame.frame_meta.instance_meta, sop_instance_uid="other")),
                    replace(frame.frame_meta, geometry=replace(frame.frame_meta.geometry, image_position_patient=(1, 2, 3)))]:
        deliver_frame(view, replace(frame, frame_meta=changed))
        assert view.mtfController.status == "empty"
        assert not view.mtfController.roiController.measurementItems
    deliver_frame(view, frame)
    assert view.mtfController.status == "ready"
    assert len(jobs) == 2


@pytest.mark.parametrize("action", ["delete", "reset", "global", "close"])
def test_late_result_after_removal_is_ignored(mtf_viewport, monkeypatch, action):
    view, _ = mtf_viewport
    jobs = capture_tasks(view, monkeypatch)
    draw(view)
    if action == "delete":
        view.deleteSelectedMeasurement()
    elif action == "reset":
        view.reset_tool_state(ToolType.SERVICE)
    elif action == "global":
        view.reset_all_view_state()
    else:
        view.shutdown()
    finish(view, jobs[0])
    assert view.mtfController.currentResult == {}
    assert not view.mtfController.roiController.committed_measurements


def test_failed_current_roi_hides_previous_result_and_no_spacing_fallback(mtf_viewport, monkeypatch):
    view, frame = mtf_viewport
    jobs = capture_tasks(view, monkeypatch)
    draw(view)
    finish(view, jobs[0])
    draw(view, (8, 8), (-10, -10))
    assert view.mtfController.status == "error" and "超出" in view.mtfController.error
    assert view.mtfController.currentResult == {}
    assert len(jobs) == 1
    no_spacing = replace(frame, frame_meta=replace(frame.frame_meta,
                         instance_meta=replace(frame.frame_meta.instance_meta, pixel_spacing=None)))
    deliver_frame(view, no_spacing)
    draw(view, (20, 20), (110, 110))
    assert "PixelSpacing" in view.mtfController.error
    assert len(jobs) == 1


def test_reset_mtf_clears_all_slices_but_not_normal_measurements(mtf_viewport, monkeypatch):
    view, frame = mtf_viewport
    capture_tasks(view, monkeypatch)
    draw(view)
    deliver_frame(view, replace(frame, frame_meta=replace(frame.frame_meta, slice_index=1)))
    draw(view)
    view._tool_controller.selectInteraction("measure:rect")
    draw(view)
    saved = view.measurementController.measurementItems
    view._tool_controller.selectService("service:mtf")
    view.reset_tool_state(ToolType.SERVICE)
    assert not view.mtfController.roiController.committed_measurements
    assert view.measurementController.measurementItems == saved
    view.reset_all_view_state()
    assert not view.measurementController.committed_measurements


@pytest.mark.parametrize("tab_type", [TabType.MPR, TabType.THREE_D, TabType.FOUR_D, TabType.TAG])
def test_direct_mtf_interaction_cannot_bypass_tab_gate(tab_type):
    tools = ToolController(tab_type=tab_type)
    initial_interaction = tools.activeInteraction
    tools.selectInteraction("service:mtf")
    assert tools.activeInteraction == initial_interaction


def test_snapshot_is_independent_of_subsequent_source_mutation(mtf_viewport, monkeypatch):
    view, frame = mtf_viewport
    jobs = capture_tasks(view, monkeypatch)
    draw(view)
    snapshot = jobs[0][1].copy()
    frame.modality_pixel[:] = 0
    np.testing.assert_array_equal(jobs[0][1], snapshot)


@pytest.mark.parametrize("action", ["delete", "page", "close"])
def test_real_inflight_worker_does_not_access_removed_or_other_slice(mtf_viewport, monkeypatch, action):
    view, frame = mtf_viewport
    started, release, finished = Event(), Event(), Event()

    def slow_compute(*args, **kwargs):
        started.set()
        assert release.wait(3)
        try:
            return compute_point_source_mtf(*args, **kwargs)
        finally:
            finished.set()

    monkeypatch.setattr(
        "qt_dicom_viewer.ui.controller.viewport.controller.mtf_controller.compute_point_source_mtf",
        slow_compute,
    )
    try:
        draw(view)
        assert started.wait(2)
        assert view.mtfController.status == "calculating"
        if action == "delete":
            view.deleteSelectedMeasurement()
        elif action == "page":
            view.apply_slice_index(1)
            deliver_frame(view, replace(frame, frame_meta=replace(frame.frame_meta, slice_index=1)))
        release.set()
        if action == "close":
            view.shutdown()
        assert finished.wait(2)
        QTest.qWait(30)
        assert view.mtfController.currentResult == {}
        assert view.mtfController.status == "empty"
    finally:
        release.set()


def test_two_viewports_with_same_slice_have_independent_rois(mtf_viewport, monkeypatch):
    first, frame = mtf_viewport
    capture_tasks(first, monkeypatch)
    second = _controller()
    try:
        second.handleRenderResult(frame)
        second._tool_controller.selectService("service:mtf")
        capture_tasks(second, monkeypatch)
        draw(first)
        assert not second.mtfController.roiController.measurementItems
        draw(second)
        first.mtfController.reset()
        assert len(second.mtfController.roiController.measurementItems) == 1
    finally:
        second.shutdown()
