from dataclasses import replace
from unittest.mock import Mock

import numpy as np
import pytest
from vtkmodules.vtkRenderingOpenGL2 import vtkGenericOpenGLRenderWindow
from vtkmodules.vtkRenderingUI import vtkGenericRenderWindowInteractor

from qt_dicom_viewer.core.volume_view import (
    VolumeViewState, face_rotation, nearest_face, view_basis, drag_volume_window,
)
from qt_dicom_viewer.model import ToolType, WindowLevel
from qt_dicom_viewer.model.render_models import VolumeLoadResult
from qt_dicom_viewer.model.volume_models import VOLUME_DIRECTIONS, VolumeDisplayState, VolumeBlendMode
from qt_dicom_viewer.volume_presets import VOLUME_PRESETS, VOLUME_PRESET_BY_ID
from qt_dicom_viewer.ui.volume_render_backend import (
    VolumeRenderBackend, create_orientation_marker, create_transfer_functions,
)
from test_volume_view import make_tab, volume  # shared synthetic volume fixture


@pytest.fixture
def loaded_tab(volume):
    tab = make_tab()
    requests = []
    tab.renderRequested.connect(requests.append)
    tab.init_render()
    request = requests[-1]
    tab.handleRenderResult(VolumeLoadResult(response_id=request.request_id,
        viewport_id=request.viewport_id, series_uid=request.series_uid, volume=volume))
    return tab


@pytest.mark.parametrize("direction", VOLUME_DIRECTIONS, ids=lambda d: d.face)
def test_standard_faces_preserve_camera_handedness_and_anatomical_up(direction):
    state = replace(VolumeViewState(), rotation=face_rotation(direction.face))
    basis = view_basis(state)
    np.testing.assert_allclose(basis[:, 2], direction.normal, atol=1e-12)
    np.testing.assert_allclose(basis[:, 1], direction.up, atol=1e-12)
    assert np.linalg.det(basis) == pytest.approx(1)
    assert nearest_face(state) == direction.face


def test_initial_anterior_and_oblique_tie_preserves_single_direction():
    assert nearest_face(VolumeViewState()) == "A"
    diagonal = VolumeViewState(rotation=(np.cos(np.pi/8), 0, np.sin(np.pi/8), 0))
    assert nearest_face(diagonal, "A") == "A"
    assert nearest_face(diagonal, "L") == "L"
    assert nearest_face(diagonal, "P") == "A"
    beyond = VolumeViewState(rotation=(np.cos(np.pi/8+0.01), 0, np.sin(np.pi/8+0.01), 0))
    assert nearest_face(beyond, "A") == "L"


def test_cube_has_six_matching_surface_colors_and_white_letters():
    assembly, labels, surface = create_orientation_marker()
    assert assembly.GetParts().GetNumberOfItems() == 2
    data = surface.GetMapper().GetInput()
    actual = set()
    for i in range(data.GetNumberOfCells()):
        points = data.GetCell(i).GetPoints()
        normal = np.mean([points.GetPoint(j) for j in range(points.GetNumberOfPoints())], axis=0)
        d = max(VOLUME_DIRECTIONS, key=lambda d: np.dot(normal, d.normal))
        rgb = tuple(data.GetCellData().GetScalars().GetTuple3(i))
        assert rgb == tuple(int(d.color[k:k+2], 16) for k in (1, 3, 5))
        actual.add(rgb)
    assert len(actual) == 6
    assert labels.GetCubeProperty().GetOpacity() == 0
    for axis, plus, minus in (("X", "L", "R"), ("Y", "P", "A"), ("Z", "S", "I")):
        for side, face in (("Plus", plus), ("Minus", minus)):
            assert getattr(labels, f"Get{axis}{side}FaceText")() == face
            assert getattr(labels, f"Get{axis}{side}FaceProperty")().GetColor() == (1, 1, 1)


@pytest.mark.parametrize("preset", VOLUME_PRESETS, ids=lambda p: p.preset_id)
def test_window_moves_color_and_opacity_together_preserving_curve_shape(preset):
    first, second = WindowLevel(center=0, width=100), WindowLevel(center=300, width=700)
    c1, a1 = create_transfer_functions(preset, first)
    c2, a2 = create_transfer_functions(preset, second)
    for t in np.linspace(0, 1, 25):
        x1, x2 = first.center+first.width*(t-0.5), second.center+second.width*(t-0.5)
        np.testing.assert_allclose(c1.GetColor(x1), c2.GetColor(x2), atol=1e-12)
        assert a1.GetValue(x1) == pytest.approx(a2.GetValue(x2))


def test_presets_have_complete_ordered_curves_and_ct_windows():
    assert len({p.preset_id for p in VOLUME_PRESETS}) == 6
    for p in VOLUME_PRESETS:
        for points in (p.colors, p.opacity):
            assert points[0][0] == 0 and points[-1][0] == 1
            assert np.all(np.diff([node[0] for node in points]) > 0)
            assert np.all((np.asarray(points) >= 0) & (np.asarray(points) <= 1))
    assert VOLUME_PRESET_BY_ID["bone"].default_window == WindowLevel(center=300, width=1500)
    assert VOLUME_PRESET_BY_ID["lung"].default_window == WindowLevel(center=-400, width=1500)
    assert VOLUME_PRESET_BY_ID["vessel"].default_window == WindowLevel(center=400, width=700)


def test_selection_windowing_and_resets_keep_independent_state(loaded_tab, volume):
    view, tools = loaded_tab.activeViewport, loaded_tab.toolController
    original_pixels = volume.modality_pixels.copy()
    view._set_state(VolumeViewState(pan=(0.2, 0.1), zoom=2))
    tools.activateTool("volume-direction")
    assert tools.activeInteraction == "volume:rotate"
    view.setViewFace("R")
    pose = view.state
    assert view.currentFace == "R" and pose.pan == (0.2, 0.1) and pose.zoom == 2
    tools.activateTool("volume-preset")
    assert tools.activeInteraction == "volume:rotate"
    view.applyVolumePreset("bone")
    assert view.state == pose and view.windowWidth == 1500
    tools.activateTool("window")
    assert tools.activeInteraction == "window" and tools.activePanel == ""
    view.begin_drag((200, 200), (800, 600))
    view.update_drag((400, 50))
    expected = WindowLevel(center=550, width=1750)
    assert view.display_state.window == expected
    view.update_drag((400, 50))  # Absolute drag offset, not cumulative increments.
    assert view.display_state.window == expected
    view.end_drag()
    assert view.state == pose and view.currentPresetId == "bone"
    tools.resetActiveTool()
    assert view.display_state.window == WindowLevel(center=300, width=1500)
    view.applyVolumePreset("lung")
    assert view.windowCenter == -400 and view.state == pose
    view._set_display_state(replace(view.display_state, window=WindowLevel(50, 100)))
    view.applyVolumePreset("lung")
    assert view.windowCenter == -400  # Selecting the same preset also resets it.
    view.reset_tool_state(ToolType.VOLUME_DIRECTION)
    assert view.currentFace == "A" and view.state.pan == pose.pan and view.currentPresetId == "lung"
    view.reset_tool_state(ToolType.VOLUME_PRESET)
    assert view.display_state == VolumeDisplayState(window=volume.default_window)
    view.applyVolumePreset("vessel")
    view.setViewFace("P")
    tools.activateTool("reset")
    assert view.state == VolumeViewState()
    assert view.display_state == VolumeDisplayState(window=volume.default_window)
    np.testing.assert_array_equal(volume.modality_pixels, original_pixels)


def test_window_drag_stops_at_one_without_inversion():
    result = drag_volume_window(WindowLevel(40, 80), (-10000, -100), (500, 500))
    assert result == WindowLevel(center=60, width=1)
    assert drag_volume_window(result, (100, 0), (500, 500)).width == 21


def test_non_ct_cannot_apply_ct_templates_or_invalid_selection(loaded_tab):
    view = loaded_tab.activeViewport
    view.viewport_config = replace(view.viewport_config,
        series_meta=replace(view.viewport_config.series_meta, modality="MR"))
    assert {p["presetId"] for p in view.volumePresets if p["available"]} == {"general", "mip", "xray"}
    for preset_id in ("bone", "lung", "vessel", "unknown"):
        view.applyVolumePreset(preset_id)
        assert view.currentPresetId == "general"
    view.setViewFace("invalid")
    assert view.currentFace == "A"
    view.applyVolumePreset("mip")
    assert view.currentPresetId == "mip"


def test_display_updates_reuse_volume_and_camera_changes_reuse_transfer_functions(volume):
    window = vtkGenericOpenGLRenderWindow()
    interactor = vtkGenericRenderWindowInteractor()
    interactor.SetRenderWindow(window)
    widget = Mock()
    widget.GetRenderWindow.return_value = window
    widget.width.return_value, widget.height.return_value = 640, 480
    backend = VolumeRenderBackend(widget)
    try:
        backend.set_volume(volume)
        data = backend.mapper.GetInput()
        expected_step = min(volume.geometry.column_spacing,
                            volume.geometry.row_spacing,
                            volume.geometry.slice_spacing)
        assert backend.mapper.GetSampleDistance() == pytest.approx(expected_step)
        assert not backend.mapper.GetInteractiveAdjustSampleDistances()
        assert not backend.mapper.GetAutoAdjustSampleDistances()
        for p in VOLUME_PRESETS:
            state = VolumeDisplayState(p.preset_id, p.default_window or volume.default_window)
            backend.apply_display(state)
            colors = backend.properties.GetRGBTransferFunction()
            stamp = colors.GetMTime()
            backend.apply_state(VolumeViewState(zoom=2))
            backend.apply_display(state)
            assert backend.properties.GetRGBTransferFunction().GetMTime() == stamp
            assert backend.mapper.GetInput() is data
            assert backend.properties.GetShade() == p.shade
            assert backend.mapper.GetBlendMode() == {
                VolumeBlendMode.COMPOSITE: 0, VolumeBlendMode.MIP: 1, VolumeBlendMode.ADDITIVE: 4,
            }[p.blend_mode]
            assert backend.mapper.GetSampleDistance() == pytest.approx(expected_step)
            assert not backend.mapper.GetInteractiveAdjustSampleDistances()
            assert not backend.mapper.GetAutoAdjustSampleDistances()
            changed = replace(state, window=WindowLevel(200, 400))
            backend.apply_display(changed)
            assert backend.properties.GetRGBTransferFunction().GetMTime() != stamp
    finally:
        backend.dispose()


def test_tabs_do_not_share_display_state(loaded_tab, volume):
    other_tab = make_tab("other")
    other = other_tab.activeViewport
    loaded_tab.activeViewport.applyVolumePreset("bone")
    assert other.currentPresetId == "general" and other.windowWidth == 0
    assert other.state == VolumeViewState()


def test_disposed_view_ignores_queued_menu_and_pointer_actions(loaded_tab):
    view = loaded_tab.activeViewport
    view.applyVolumePreset("bone")
    view.setViewFace("P")
    pose, display = view.state, view.display_state
    view.dispose()
    view.applyVolumePreset("lung")
    view.setViewFace("A")
    view.begin_drag((0, 0), (600, 600))
    view.update_drag((100, 100))
    view.wheel_zoom(120, 0)
    view.reset_tool_state(ToolType.VOLUME_PRESET)
    view.reset_all_view_state()
    assert view.state == pose and view.display_state == display
    assert view.volume is None
