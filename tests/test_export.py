from pathlib import Path
from types import SimpleNamespace
from threading import Event

import pytest
from PySide6.QtGui import QImage
import pydicom
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from qt_dicom_viewer.model import TabType
from qt_dicom_viewer.ui.controller.export_controller import copy_dicom_series, ExportController
from qt_dicom_viewer.ui.controller.tab.tool_controller import ToolController
from test_dicom_tags import qt_app, wait_until
from test_series_sidebar import sidebar_scene
from test_tag_qml import find, click, descendants


def record(paths, uid='one', phases=()):
    return SimpleNamespace(series_instance_uid=uid, phases=phases, instances=tuple(SimpleNamespace(path=p, series_instance_uid=uid) for p in paths))


def test_copy_preserves_bytes_multiframe_duplicates_and_all_phases(tmp_path):
    source = tmp_path / 'source'; source.mkdir()
    target = tmp_path / 'target'; target.mkdir()
    first, second = source / 'a.dcm', source / 'b.dcm'
    first.write_bytes(b'original pixel and tag bytes')
    second.write_bytes(b'multiframe original bytes')
    phase = record([second], 'two')
    series = record([first, first], phases=[phase])
    output, count = copy_dicom_series([series], target)
    assert count == 2
    assert (output / 'series-01/000001.dcm').read_bytes() == first.read_bytes()
    assert (output / 'series-02/000001.dcm').read_bytes() == second.read_bytes()
    again, _ = copy_dicom_series([series], target)
    assert again != output
    assert len(list(source.iterdir())) == 2


def test_copy_failure_and_cancel_do_not_leave_partial_export(tmp_path):
    source = tmp_path / 'a.dcm'; source.write_bytes(b'original')
    target = tmp_path / 'out'; target.mkdir()
    with pytest.raises(OSError):
        copy_dicom_series([record([source, tmp_path / 'missing'])], target)
    assert not list(target.iterdir())
    cancelled = Event()
    def progress(_): cancelled.set()
    with pytest.raises(InterruptedError):
        copy_dicom_series([record([source])], target, cancelled, progress)
    assert not list(target.iterdir())


@pytest.mark.parametrize('kind', [TabType.TWO_D, TabType.MPR, TabType.FOUR_D, TabType.THREE_D, TabType.MONTAGE, TabType.PETCT_FUSION])
def test_export_catalog_and_panel_are_available(kind):
    tools = ToolController(tab_type=kind)
    assert any(t['toolType'] == 'export' and t['available'] for t in tools.tools)
    tools.activateTool('export')
    assert tools.activePanel == 'export'
    assert not tools.canResetActiveTool
    assert tools.tools[-1]['toolType'] == 'reset'


@pytest.mark.parametrize('anonymous', [True, False])
@pytest.mark.parametrize('width, kind', [(1000, TabType.TWO_D), (1400, TabType.TWO_D), (1400, TabType.MPR), (1400, TabType.MONTAGE)])
def test_real_export_buttons_save_viewport_png_and_original_dicom(sidebar_scene, monkeypatch, tmp_path, width, kind, anonymous):
    window, app, records, warnings = sidebar_scene
    window.resize(width, 800)
    ws = app.workspaceController
    ws.createTab(records[0].series_instance_uid, 'Export demo', kind)
    if kind == TabType.MONTAGE:
        wait_until(lambda: ws.activeViewport.sliceCount > 0)
    else:
        wait_until(lambda: ws.activeViewport.loadState in ('ready', 'error'), timeout=15000)
        assert ws.activeViewport.loadState == 'ready', ws.activeViewport.errorMessage
    wait_until(lambda: ws.activeLoadState.status == "ready", timeout=15000)
    if kind == TabType.MPR:
        coronal = next(v for v in ws.activeTab.viewports_by_id.values()
                       if v.viewport_config.viewport_type == 'coronal')
        ws.activeTab.activateViewport(coronal.viewport_config.viewport_id)
    QTest.qWait(100)
    click(window, find(window, 'primaryTool-export'))
    assert ws.activeTab.toolController.activePanel == 'export'
    right = find(window, 'rightPanel')
    item = right.property('exportItem')
    assert item is not None and item.width() < window.width()
    checkbox = find(window, 'viewportExportAnonymous')
    assert checkbox.property('checked')  # A newly opened export panel starts anonymous.
    if not anonymous:
        click(window, checkbox)
    png = tmp_path / 'frame.png'
    monkeypatch.setattr('qt_dicom_viewer.ui.controller.export_controller.QFileDialog.getSaveFileName', lambda *args: (str(png), 'PNG'))
    click(window, find(window, 'exportPng'))
    wait_until(lambda: not app.exportController.busy)
    assert not app.exportController.isError, app.exportController.message
    image = QImage(str(png))
    assert not image.isNull()
    assert image.width() == round(item.width() * window.devicePixelRatio())
    assert image.height() == round(item.height() * window.devicePixelRatio())
    assert any(image.pixelColor(x, y).lightness() > 20 for x in range(0, image.width(), 10) for y in range(0, image.height(), 10))
    target = tmp_path / 'dicom'; target.mkdir()
    monkeypatch.setattr('qt_dicom_viewer.ui.controller.export_controller.QFileDialog.getExistingDirectory', lambda *args: str(target))
    click(window, find(window, 'exportDicom'))
    wait_until(lambda: not app.exportController.busy)
    assert not app.exportController.isError, app.exportController.message
    exported = sorted(target.rglob('*.dcm'))
    assert len(exported) == len(records[0].instances)
    if anonymous:
        assert not image.textKeys()
        assert not item.property('anonymousExport')  # Live preferences restored after capture.
        for path, instance in zip(exported, records[0].instances):
            result, source = pydicom.dcmread(path), pydicom.dcmread(instance.path)
            assert result.PatientName == 'ANONYMOUS' and result.PatientIdentityRemoved == 'YES'
            assert result.PatientID != source.PatientID
            assert result.StudyInstanceUID != source.StudyInstanceUID
            assert result.SeriesInstanceUID != source.SeriesInstanceUID
            assert result.PixelData == source.PixelData
    else:
        assert [p.read_bytes() for p in exported] == [i.path.read_bytes() for i in records[0].instances]
    assert find(window, 'exportMessage').property('text')
    assert window.grabWindow().save(str(tmp_path / f'export-{width}.png'))
    monkeypatch.setattr('qt_dicom_viewer.ui.controller.export_controller.QFileDialog.getSaveFileName', lambda *args: ('', ''))
    click(window, find(window, 'exportPng'))
    assert '取消' in app.exportController.message and not app.exportController.busy
    assert not warnings, warnings
    # Releasing the captured item must not invalidate its owning window.
    del item
    import shiboken6
    assert shiboken6.isValid(window)


def test_failed_png_does_not_replace_existing_file(qt_app, tmp_path):
    target = tmp_path / 'existing.png'
    target.write_bytes(b'keep original')
    exporter = ExportController(None, None)
    exporter._start('Exporting')
    exporter._save_png(QImage(), target)
    assert exporter.isError and not exporter.busy
    assert target.read_bytes() == b'keep original'
    exporter.shutdown()


def test_background_export_survives_tab_changes_and_reports_failure(qt_app, tmp_path):
    exporter = ExportController(None, None)
    exporter.export_dicom_to([record([tmp_path / 'missing.dcm'])], tmp_path)
    # Jobs retain source records, not the active tab or its QML objects.
    exporter.workspace = None
    wait_until(lambda: not exporter.busy)
    assert exporter.isError and '失败' in exporter.message
    assert not list(tmp_path.iterdir())
    exporter.shutdown()
