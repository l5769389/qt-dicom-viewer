from copy import deepcopy
from dataclasses import replace
import json

import numpy as np
import pytest
from PySide6.QtCore import QSize

from qt_dicom_viewer.core.color_maps import apply_color_map, color_lut, COLOR_MAPS
from qt_dicom_viewer.settings.preferences import DEFAULTS, normalize_settings
from qt_dicom_viewer.ui.controller.settings_controller import SettingsController
from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
from qt_dicom_viewer.ui.controller.viewport.image_2d.mpr_viewport_controller import MprViewportController
from qt_dicom_viewer.model import MprPlane
from test_viewport_transform import _controller, _render_result


def test_settings_persist_validate_and_restore_one_section(tmp_path):
    path = tmp_path / 'display.json'
    settings = SettingsController(path=path)
    assert settings.setValue('scale', 'enabled', False)
    assert settings.setValue('corners', 'color', '#12ABef')
    assert settings.setValue('roi', 'mean', False)
    before = path.read_bytes()
    for section, key, value in [('scale', 'color', 'red'), ('corners', 'fontSize', 0),
                                ('measurement', 'lineWidth', float('nan')), ('roi', 'mean', 'false'),
                                ('colormap', 'gray', 'missing')]:
        assert not settings.setValue(section, key, value)
        assert path.read_bytes() == before
    loaded = SettingsController(path=path)
    assert loaded.values == settings.values
    assert loaded.resetSection('scale')
    assert loaded.values['scale'] == DEFAULTS['scale']
    assert loaded.values['corners']['color'] == '#12abef'
    assert not loaded.values['roi']['mean']
    values = loaded.values
    values['scale']['enabled'] = False
    assert loaded.values['scale']['enabled']  # QML gets a snapshot, not mutable backing state.


def test_malformed_settings_recover_and_save_failure_keeps_current_state(tmp_path):
    path = tmp_path / 'display.json'
    path.write_text('{broken')
    settings = SettingsController(path=path)
    assert settings.values == DEFAULTS and settings.message
    raw = deepcopy(DEFAULTS)
    raw['scale']['color'] = 'bad'
    raw['roi']['mean'] = False
    assert normalize_settings(raw)['roi']['mean'] is False
    assert normalize_settings(raw)['scale'] == DEFAULTS['scale']
    directory = tmp_path / 'directory'
    directory.mkdir()
    settings = SettingsController(path=directory)
    assert not settings.setValue('scale', 'enabled', False)
    assert settings.values['scale']['enabled']


def test_window_templates_crud_validation_and_enabled_list(tmp_path):
    settings = SettingsController(path=tmp_path / 'display.json')
    assert settings.saveWindowTemplate('', 'Custom Lung', 1200, -500)
    custom = settings.values['window']['custom'][0]
    assert not settings.saveWindowTemplate('', 'custom lung', 100, 0)
    assert not settings.saveWindowTemplate('', 'Invalid', 0, 0)
    assert settings.enableWindowTemplate('ct-lung', False)
    assert settings.enableWindowTemplate(custom['presetId'], False)
    assert settings.saveWindowTemplate(custom['presetId'], 'Updated', 900, -400)
    assert all(p['presetId'] not in ('ct-lung', custom['presetId']) for p in settings.window_presets)
    assert settings.enableWindowTemplate(custom['presetId'], True)
    assert settings.window_presets[-1]['width'] == 900
    assert SettingsController(path=tmp_path / 'display.json').window_presets == settings.window_presets
    assert settings.deleteWindowTemplate(custom['presetId'])
    assert not settings.values['window']['custom']


def test_corner_fields_reorder_remove_and_capacity():
    settings = SettingsController(path=False)
    assert settings.addCornerField('topRight', 'zoom')
    assert settings.moveCornerField('topRight', 2, -1)
    assert settings.values['corners']['topRight'] == ['patientName', 'zoom', 'patientId']
    assert settings.removeCornerField('topRight', 0)
    assert not settings.addCornerField('topRight', 'zoom')
    assert not settings.setValue('corners', 'topLeft', ['missing'])
    for field in ('manufacturer', 'modality', 'window', 'cursor', 'matrix', 'spacing'):
        assert settings.addCornerField('topRight', field)
    assert not settings.addCornerField('topRight', 'slice')


@pytest.mark.parametrize('name', COLOR_MAPS)
def test_lut_display_pixels_leave_source_data_unchanged(name):
    source = np.arange(256, dtype=np.uint8).reshape(16, 16)
    original = source.copy()
    colored = apply_color_map(source, name)
    np.testing.assert_array_equal(source, original)
    if name == 'grayscale':
        assert colored is source
    else:
        assert colored.shape == (16, 16, 3)
        np.testing.assert_array_equal(colored[0, 0], color_lut(name)[0])
        np.testing.assert_array_equal(colored[-1, -1], color_lut(name)[255])
    provider = DicomImageProvider()
    provider.set_array('lut', colored)
    image = provider.requestImage('lut/1', QSize(), QSize())
    assert image.width() == 16 and image.height() == 16
    if name == 'bwInverse':
        assert image.pixelColor(0, 0).red() == 255
        assert image.pixelColor(15, 15).red() == 0
    if name == 'hotIron':
        assert image.pixelColor(8, 8).red() > image.pixelColor(8, 8).blue()


def test_settings_reach_open_viewports_and_render_requests():
    controller = _controller()
    controller.handleRenderResult(_render_result(controller))
    settings = controller.settingsController
    requests = []
    controller.renderRequested.connect(requests.append)
    assert settings.setValue('colormap', 'gray', 'bwInverse')
    assert controller.colorMap == 'bwInverse' and controller.canvasBackgroundColor == '#ffffff'
    assert requests[-1].color_map == 'bwInverse'
    original_pixels = controller._modality_pixel.copy()
    settings.setValue('roi', 'mean', False)
    np.testing.assert_array_equal(controller._modality_pixel, original_pixels)
    config = replace(controller.viewport_config, viewport_id='mpr', viewport_type=MprPlane.CORONAL)
    mpr = MprViewportController(config, controller._tool_controller)
    settings.setValue('crosshair', 'axialColor', '#123456')
    settings.setValue('crosshair', 'axialWidth', 4.5)
    assert mpr.crosshairStyle['horizontalColor'] == '#123456'
    assert mpr.crosshairStyle['horizontalWidth'] == 4.5
    assert mpr._build_render_request(initial=True).color_map == 'bwInverse'
    controller.shutdown()


def test_palette_changes_while_first_frame_pending_request_latest_color():
    controller = _controller()
    requests = []
    controller.renderRequested.connect(requests.append)
    assert controller._frame_meta is None
    controller.settingsController.setValue('colormap', 'gray', 'pet')
    assert requests[-1].color_map == 'pet'
    assert requests[-1].window is None
    controller.shutdown()


def test_arrow_and_measurement_resets_are_separate():
    from qt_dicom_viewer.model import MeasurementKind
    from qt_dicom_viewer.ui.controller.viewport.controller.measure.measure_controller import MeasurementController
    from test_measurement_controller import _context, _position, _drag
    controller = MeasurementController()
    for kind, y in [(MeasurementKind.LENGTH, 10), (MeasurementKind.ARROW, 30)]:
        start, end = _position(0, y), _position(10, y)
        controller.begin(start, replace(_context(), measurement_kind=kind))
        controller.update(_drag(start, end))
        controller.end(end)
    assert {item['type'] for item in controller.measurementItems} == {'length', 'arrow'}
    controller.clear_kind(arrows=False)
    assert [item['type'] for item in controller.measurementItems] == ['arrow']
    controller.clear_kind(arrows=True)
    assert controller.measurementItems == []
