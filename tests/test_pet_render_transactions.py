from dataclasses import replace
from threading import Event

import pytest

from test_pet_2d import _pet_dataset, _write_dataset, _pet_render_result, _pet_viewport
from test_measurement_qml import qt_app
from test_dicom_tags import wait_until
from qt_dicom_viewer.model import StackRenderRequest, RenderFailure, WindowLevel
from qt_dicom_viewer.core.dicom_loader import DicomLoader
from qt_dicom_viewer.core.volume_manager import VolumeManager
from qt_dicom_viewer.application.series_catalog import SeriesCatalog
from qt_dicom_viewer.service.render_serivce import RenderService


def test_stack_decode_cache_reused_for_unit_and_window(tmp_path, monkeypatch):
    path = _write_dataset(_pet_dataset(), tmp_path / "pet.dcm")
    loader = DicomLoader()
    decode = loader.to_modality_pixels
    count = []
    def counted(dataset):
        count.append(dataset.SOPInstanceUID)
        return decode(dataset)
    monkeypatch.setattr(loader, "to_modality_pixels", counted)
    request = StackRenderRequest(request_id="a", viewport_id="v", series_uid="s", slice_index=0,
                                  window=None, inverted=False)
    loader.load_a_dicom(path, request)
    result = loader.load_a_dicom(path, replace(request, value_unit="kbqml", window=WindowLevel(1, 2)))
    assert len(count) == 1
    assert result.pixel_value_meta.unit == "kBq/ml"


def test_pet_stack_stale_success_failure_and_pending_reset():
    viewport, _ = _pet_viewport()
    initial = _pet_render_result()
    viewport.handleRenderResult(initial)
    requests = []
    viewport.renderRequested.connect(requests.append)
    viewport.setPetUnit("kbqml")
    old = requests[-1]
    viewport.setPetUnit("source")
    latest = requests[-1]
    viewport.handleRenderResult(replace(initial, response_id=old.request_id))
    viewport.handleRenderFailure(RenderFailure(request_id=old.request_id, viewport_id=viewport.viewportId,
                                               error=ValueError("old")))
    assert viewport.petUnitPending and viewport.petActiveUnitId == "suvbw"
    viewport.handleRenderFailure(RenderFailure(request_id=latest.request_id, viewport_id=viewport.viewportId,
                                               error=ValueError("new")))
    assert not viewport.petUnitPending
    assert viewport.petActiveUnitId == "suvbw"
    assert viewport.petControlUpperOptions == [5., 10., 20., 30., 40.]
    assert viewport._modality_pixel is initial.modality_pixel
    viewport.setPetControlUpper(30.00001)
    assert 30.00001 in viewport.petControlUpperOptions


@pytest.mark.parametrize("fail_first", [False, True])
def test_render_queue_has_only_running_and_latest_request(qt_app, monkeypatch, fail_first):
    entered, release = Event(), Event()
    service = RenderService(SeriesCatalog(), VolumeManager())
    completed, failed, reads = [], [], []
    service.rendered.connect(completed.append)
    service.failed.connect(failed.append)
    def render(request):
        reads.append(request.request_id)
        if request.request_id == "first":
            entered.set()
            assert release.wait(3)
            if fail_first:
                service._worker.render_failed.emit(RenderFailure(request_id=request.request_id,
                    viewport_id=request.viewport_id, error=ValueError("obsolete")))
                return
        service._worker.render_finished.emit(replace(_pet_render_result(),
            response_id=request.request_id, viewport_id=request.viewport_id))
    monkeypatch.setattr(service._worker, "_handle_stack_request", render)
    request = StackRenderRequest(request_id="first", viewport_id="v", series_uid="s", slice_index=0,
                                  window=None, inverted=False)
    try:
        service.submit(request)
        wait_until(entered.is_set)
        for i in range(100):
            service.submit(replace(request, request_id=str(i)))
        assert len(service._pending) == 1
        release.set()
        wait_until(lambda: len(completed) == 1)
        assert reads == ["first", "99"]
        assert completed[0].response_id == "99"
        assert not failed
    finally:
        release.set()
        service.shutdown()
