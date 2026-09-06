"""Regressions at the boundaries between the merged feature branches."""
from dataclasses import replace

import numpy as np

from qt_dicom_viewer.core.color_maps import color_lut
from qt_dicom_viewer.core.pet_reconstruction import PetReconstructor
from qt_dicom_viewer.core.volume_manager import VolumeManager
from qt_dicom_viewer.ui.controller.settings_controller import SettingsController
from qt_dicom_viewer.ui.controller.workspace_controller import WorkspaceController
from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
from test_measurement_qml import qt_app
from test_pet_fusion import paired_series
from test_viewport_transform import _controller, _render_result


def test_ct_rejects_stale_frame_after_latest_frame_is_committed(qt_app):
    view = _controller()
    try:
        view.handleRenderResult(_render_result(view))
        view.request_render()
        old_id = view._latest_request_id
        view.request_render()
        current = replace(_render_result(view), response_id=view._latest_request_id)
        view.handleRenderResult(current)
        revision = view._image_revision
        stale = replace(current, response_id=old_id,
                        modality_pixel=np.full_like(current.modality_pixel, 999))
        view.handleRenderResult(stale)
        assert view._image_revision == revision
        assert view._modality_pixel is current.modality_pixel
    finally:
        view.shutdown()


def test_settings_and_viewport_palettes_share_pet_fusion_transaction(qt_app, paired_series):
    catalog, ct, pet = paired_series
    workspace = WorkspaceController(catalog, DicomImageProvider())
    workspace._settings_controller = SettingsController(workspace, path=False)
    renderer = PetReconstructor(catalog, VolumeManager())
    requests, results = [], []

    def render(request):
        requests.append(request)
        result = renderer.render(request)
        results.append(result)
        workspace.handleRenderResult(result)

    workspace.renderRequested.connect(render)
    try:
        workspace.createFusionTab(ct.series_instance_uid, pet.series_instance_uid)
        tab = workspace.activeTab
        viewport = tab.petController
        previous = viewport._modality_pixel.copy()
        request_count = len(requests)
        workspace._settings_controller.setValue("colormap", "pet", "pet")
        assert len(requests) == request_count + 1
        assert requests[-1].pet_color_map == "pet"
        np.testing.assert_equal(viewport._modality_pixel, previous)
        assert viewport.activeColorMap == "pet"
        pet_frame = next(frame for frame in results[-1].frames if frame.viewport_id == viewport.viewportId)
        assert pet_frame.image.ndim == 3

        # The earlier viewport branch uses this legacy palette identifier.
        viewport.applyColorMap("cardiac")
        assert requests[-1].pet_color_map == "cardiac"
        assert viewport.activeColorMap == "cardiac"
        np.testing.assert_equal(viewport._modality_pixel, previous)
        fusion = next(v for v in tab.viewports_by_id.values() if v.viewportRole == "fusion")
        fusion.applyColorMap("hotMetal")
        assert requests[-1].fusion_color_map == "hotMetal"
        assert fusion.activeColorMap == "hotMetal"
        mip = next(v for v in tab.viewports_by_id.values() if v.viewportRole == "mip")
        assert mip.activeColorMap == "cardiac"
        assert color_lut("cardiac").shape == (256, 3)
    finally:
        workspace.shutdown()


def test_window_template_updates_notify_open_ct_but_leave_pet_presets_empty(qt_app, paired_series):
    catalog, ct, pet = paired_series
    workspace = WorkspaceController(catalog, DicomImageProvider())
    workspace._settings_controller = SettingsController(workspace, path=False)
    try:
        workspace.createTab(ct.series_instance_uid, "CT", "2d")
        ct_view = workspace.activeViewport
        workspace.createTab(pet.series_instance_uid, "PET", "2d")
        pet_view = workspace.activeViewport
        updates = []
        ct_view.windowPresetsChanged.connect(lambda: updates.append(True))
        workspace._settings_controller.saveWindowTemplate("", "Integration window", 321, 12)
        assert updates
        assert ct_view.windowPresets[-1]["width"] == 321
        assert pet_view.windowPresets == []
    finally:
        workspace.shutdown()
