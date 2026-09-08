import numpy as np
import pytest

from test_pet_volume import fusion_scene
from test_pet_fusion import paired_series
from test_measurement_qml import qt_app


@pytest.mark.parametrize("tool", ["window", "pan", "measure:rect", "annotate:text", "registration"])
def test_locator_press_has_priority_and_preserves_arm_offset(fusion_scene, tool):
    _, source, renderer, requests = fusion_scene
    view = next(v for v in source.viewports_by_id.values() if v.viewportRole == "fusion")
    if tool == "registration":
        source.setRegistrationActive(True)
    else:
        source.toolController.selectInteraction(tool)
    geometry, center = view._plane_geometry, view._crosshair_image_position
    matrix, window = source.matrix.copy(), view.current_window
    # Grab an arm near the center, not exactly the center pixel.
    column, row = center.column+.03, center.row
    assert view.captureLocatorPress(100, 100, 1, True, column, row, .02, .01)
    view.beginInteraction(100, 100, 1, True, column, row, .02, .01)
    assert view._locator_drag is not None and view._registration_drag is None
    assert view._active_drag_operation is None and not view._annotation_drag_active
    assert view.updateRegistrationDrag(column+.4, row+.3)
    expected = geometry.image_point_to_patient(column=center.column+.4, row=center.row+.3)
    np.testing.assert_allclose(source._target_mpr_state.frame.center_patient, expected)
    source.handleRenderResult(renderer.render(requests[-1]))
    # Fresh geometry arriving mid-gesture must not move the grabbed point.
    view.endInteraction(120, 115, True, column+.8, row+.6)
    expected = geometry.image_point_to_patient(column=center.column+.8, row=center.row+.6)
    np.testing.assert_allclose(source._target_mpr_state.frame.center_patient, expected)
    np.testing.assert_array_equal(source.matrix, matrix)
    assert view.current_window == window
    assert view._locator_drag is None


def test_press_outside_locator_cannot_be_stolen_by_later_render(fusion_scene):
    _, source, renderer, requests = fusion_scene
    view = source.activeViewport
    source.toolController.selectInteraction("pan")
    g, center = view._plane_geometry, view._crosshair_image_position
    column, row = center.column+.5, center.row+.5
    assert not view.captureLocatorPress(100, 100, 1, True, column, row, .02, .01)
    source.move_center(g.image_point_to_patient(column=column, row=row))
    source.handleRenderResult(renderer.render(requests[-1]))
    view.beginInteraction(100, 100, 1, True, column, row, .02, .01)
    assert view._locator_drag is None
    assert view._active_drag_operation is view._pan_operation
    view.endInteraction(100, 100, True, column, row)


@pytest.mark.parametrize("plane", ["axial", "coronal", "sagittal"])
def test_linked_planes_keep_quantitative_ct_on_fusion_grid(fusion_scene, plane):
    _, source, renderer, requests = fusion_scene
    views = {v.viewportRole: v for v in source.viewports_by_id.values()}
    source.setPlane(plane)
    result = renderer.render(requests[-1])
    source.handleRenderResult(result)
    assert {views[r].viewportType for r in ("ct", "pet", "fusion")} == {plane}
    fusion = next(frame for frame in result.frames if frame.viewport_id == views["fusion"].viewportId)
    expected_ct = renderer.reslicer._sample_plane(result.ct_volume, fusion.plane_geometry)
    np.testing.assert_allclose(views["fusion"].measurementController.secondary_pixels, expected_ct)
    assert expected_ct.shape == fusion.modality_pixel.shape
    views["ct"].apply_zoom(2)
    assert {views[r].zoom for r in ("ct", "pet", "fusion")} == {2}
    assert len({views[r]._plane_geometry for r in ("ct", "pet", "fusion")}) == 1
    assert not hasattr(source, "setLinkedPlanes") and not hasattr(source, "setViewportPlane")


def test_mip_locator_uses_peak_depth_and_ignores_preview(fusion_scene):
    from dataclasses import replace
    _, source, _, _ = fusion_scene
    mip = next(v for v in source.viewports_by_id.values() if v.viewportRole == "mip")
    source.setRegistrationActive(True)
    result, center = mip._mip_result, mip.crosshairImagePosition
    r, c = np.unravel_index(np.nanargmax(result.modality_pixel), result.modality_pixel.shape)
    matrix = source.matrix.copy()
    assert mip.captureLocatorPress(0, 0, 1, True, center.x()+.03, center.y(), .02, .01)
    mip.beginInteraction(0, 0, 1, True, center.x()+.03, center.y(), .02, .01)
    assert mip.updateRegistrationDrag(c+.03, r)
    mip.endInteraction(0, 0, True, c+.03, r)
    np.testing.assert_allclose(source._target_mpr_state.frame.center_patient, result.peak_positions[r, c])
    np.testing.assert_array_equal(source.matrix, matrix)
    mip._mip_result = replace(result, preview=True)
    center = mip.crosshairImagePosition
    assert not mip.captureLocatorPress(0, 0, 1, True, center.x(), center.y(), 1, 1)
