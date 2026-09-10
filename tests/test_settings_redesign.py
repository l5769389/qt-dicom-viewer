"""Exercise the redesigned settings through real QML input and rendered pixels."""
from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, Qt, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest
from shiboken6 import delete

from test_dicom_tags import qt_app
from test_pacs_qml import scene
from test_tag_qml import find, click, type_text, descendants
from test_ui_polish import inside_width


def open_page(scene, category, width=1400):
    window, app, warnings = scene
    window.resize(width, 900)
    app.workspaceController.openSettings()
    app.settingsController.selectCategory(category)
    # The asynchronous page may be visible before its nested layouts polish.
    find(window, 'settingsPage')
    assert not window.grabWindow().isNull()
    return window, app, warnings


def test_corner_editor_switch_reorder_remove_add_and_preview(scene):
    window, app, warnings = open_page(scene, 'corners')
    settings = app.settingsController
    original = settings.values['corners']['topLeft'][:]
    click(window, find(window, 'cornerDown-topLeft-0'))
    assert settings.values['corners']['topLeft'] == [original[1], original[0], *original[2:]]
    click(window, find(window, 'cornerRemove-topLeft-0'))
    assert settings.values['corners']['topLeft'] == [original[0], *original[2:]]
    click(window, find(window, 'cornerSelect-topRight'))
    before = settings.values['corners']['topRight'][:]
    assert not find(window, 'cornerUp-topRight-0').isEnabled()
    choice = find(window, 'cornerChoice-topRight')
    chosen = choice.property('currentValue')
    assert chosen not in before
    click(window, find(window, 'cornerAdd-topRight'))
    assert settings.values['corners']['topRight'] == [*before, chosen]
    assert find(window, 'cornerChoice-topRight').property('currentValue') not in [*before, chosen]
    click(window, find(window, 'cornerPreview-bottomRight'))
    assert find(window, 'cornerSelect-bottomRight').property('checked')
    assert find(window, 'cornerRemove-bottomRight-0').isEnabled()
    assert not warnings, warnings


@pytest.mark.parametrize('width', [1000, 1400])
def test_color_popup_click_escape_and_persistence(scene, width):
    window, app, warnings = open_page(scene, 'measurement', width)
    picker = find(window, 'colorPicker-measurement-editingColor')
    click(window, picker)
    colors = [i for i in descendants(window.contentItem()) if i.isVisible() and i.objectName().startswith('colorChoice-measurement-editingColor-')]
    assert len(colors) == 8
    for color in colors:
        inside_width(color, window.contentItem())
    click(window, find(window, 'colorChoice-measurement-editingColor-22c55e'))
    assert app.settingsController.values['measurement']['editingColor'] == '#22c55e'
    assert not any(i.isVisible() for i in colors)
    assert find(window, 'setting-measurement-editingColor').property('text') == '#22c55e'
    click(window, picker)
    QTest.keyClick(window, Qt.Key_Escape)
    assert not any(i.isVisible() for i in colors)
    assert not warnings, warnings


def test_numeric_input_updates_preview_and_restores_invalid_input(scene):
    window, app, warnings = open_page(scene, 'measurement')
    field = find(window, 'settingInput-measurement-lineWidth')
    type_text(window, field, '2.75')
    QTest.keyClick(window, Qt.Key_Tab)
    assert app.settingsController.values['measurement']['lineWidth'] == 2.75
    # Invalid intermediate input must not remain displayed after losing focus.
    type_text(window, field, '9')
    QTest.keyClick(window, Qt.Key_Tab)
    assert field.property('text') == '2.75'
    assert app.settingsController.values['measurement']['lineWidth'] == 2.75
    type_text(window, field, '')
    QTest.keyClick(window, Qt.Key_Tab)
    assert field.property('text') == '2.75'
    slider = find(window, 'setting-measurement-lineWidth')
    slider.forceActiveFocus()
    QTest.keyClick(window, Qt.Key_Right)
    assert app.settingsController.values['measurement']['lineWidth'] > 2.75
    assert not warnings, warnings


@pytest.mark.parametrize('width', [1000, 1400, 2000])
def test_window_table_columns_align_and_editor_stays_compact(scene, width, tmp_path):
    window, app, warnings = open_page(scene, 'window', width)
    for suffix in ['WW', 'WL']:
        header = find(window, 'windowHeader' + suffix)
        right = header.mapToScene(QPointF(header.width(), 0)).x()
        cells = [i for i in descendants(window.contentItem()) if i.isVisible() and i.objectName().startswith('window' + suffix + '-')]
        assert len(cells) == 4
        for cell in cells:
            assert cell.mapToScene(QPointF(cell.width(), 0)).x() == pytest.approx(right, abs=1)
    for field_name in ['windowTemplateWidth', 'windowTemplateCenter']:
        assert find(window, field_name).width() <= 100
    type_text(window, find(window, 'windowTemplateName'), 'Review preset')
    click(window, find(window, 'saveWindowTemplate'))
    identifier = app.settingsController.values['window']['custom'][0]['presetId']
    click(window, find(window, 'windowEdit-' + identifier))
    type_text(window, find(window, 'windowTemplateCenter'), '-100')
    click(window, find(window, 'saveWindowTemplate'))
    assert app.settingsController.values['window']['custom'][0]['center'] == -100
    assert window.grabWindow().save(str(tmp_path / f'window-{width}.png'))
    click(window, find(window, 'windowDelete-' + identifier))
    assert not app.settingsController.values['window']['custom']
    assert not warnings, warnings


@pytest.mark.parametrize('category', ['crosshair', 'corners', 'scale', 'measurement', 'roi'])
def test_settings_preview_remains_bounded_on_wide_screens(scene, category, tmp_path):
    window, app, warnings = open_page(scene, category, 2000)
    preview = find(window, 'settingsPreviewColumn')
    form = find(window, 'settingsParameterColumn')
    assert 240 <= preview.width() <= 280
    assert preview.height() > 80
    assert preview.mapToScene(QPointF()).x() > form.mapToScene(QPointF()).x() + form.width()
    for item in descendants(window.contentItem()):
        if item.isVisible() and item.objectName().startswith(('setting-', 'settingInput-', 'cornerSelect-', 'colorPicker-')):
            inside_width(item, form)
    assert window.grabWindow().save(str(tmp_path / f'{category}-2000.png'))
    assert not warnings, warnings


@pytest.mark.parametrize('size', [24, 28, 48])
def test_mpr_crosshair_and_color_mapping_are_legible_at_toolbar_sizes(qt_app, size, tmp_path):
    view = QQuickView()
    from qt_dicom_viewer.ui.svg_icon_provider import SvgIconProvider
    view.engine().addImageProvider("navigation", SvgIconProvider())
    warnings = []
    view.engine().warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    view.setColor(QColor('black'))
    view.setInitialProperties({'iconName': 'nav-view-mpr', 'iconSize': size})
    view.setSource(QUrl.fromLocalFile(str(Path(__file__).resolve().parents[1] / 'src/qt_dicom_viewer/qml/components/AppIcon.qml')))
    assert view.status() == QQuickView.Ready
    view.show()
    try:
        QTest.qWait(80)
        frame = view.grabWindow()
        # The reference point and all four crosshair arms remain visible at toolbar size.
        middle_x, middle_y = frame.width() // 2, frame.height() // 2
        assert frame.pixelColor(middle_x, middle_y).lightness() > 50
        for x, y in [(middle_x, size // 5), (middle_x, size * 4 // 5),
                     (size // 5, middle_y), (size * 4 // 5, middle_y)]:
            assert any(frame.pixelColor(x + dx, y + dy).lightness() > 50
                       for dx in [-1, 0, 1] for dy in [-1, 0, 1])
        assert frame.save(str(tmp_path / f'mpr-{size}.png'))
        view.rootObject().setProperty('iconName', 'pseudocolor')
        QTest.qWait(80)
        frame = view.grabWindow()
        pixels = [frame.pixelColor(x, y) for x in range(frame.width()) for y in range(frame.height())]
        # Both a grayscale ramp and warm/cool colored pixels survive downscaling.
        assert sum(c.lightness() > 80 and c.saturation() < 60 for c in pixels) >= 8
        assert sum(c.red() > c.blue() + 35 for c in pixels) >= 8
        assert sum(c.blue() > c.red() + 35 for c in pixels) >= 8
        assert frame.save(str(tmp_path / f'pseudocolor-{size}.png'))
        assert not warnings, warnings
    finally:
        view.hide()
        delete(view)
