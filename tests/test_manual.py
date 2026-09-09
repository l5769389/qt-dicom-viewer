"""Offline manual resources, singleton navigation and real workspace rendering."""
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtTest import QTest

from qt_dicom_viewer.ui.controller.manual_tab_controller import ManualTabController, manual_content
from qt_dicom_viewer.ui.svg_icon_provider import render_icon
from test_dicom_tags import qt_app, wait_until
from test_pacs_qml import scene
from test_series_sidebar import sidebar_scene
from test_tag_qml import find, click, type_text, descendants

ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / 'src/qt_dicom_viewer/qml'


def test_manual_content_and_bundled_resources(qt_app):
    content = manual_content()
    categories = {c['id'] for c in content['categories']}
    chapters = content['chapters']
    assert len(categories) == 8 and len({c['id'] for c in chapters}) == len(chapters) == 31
    resources = {f.text for f in ET.parse(ROOT / 'Voxenra.qrc').iter('file')}
    expected = {'assets/help/manual.json', 'assets/icons/manual.svg'}
    for chapter in chapters:
        assert chapter['category'] in categories
        assert chapter['title'] and all(s['title'] and s['body'] for s in chapter['sections'])
        for example in chapter.get('examples', []) + ([chapter['example']] if chapter.get('example') else []):
            expected.add('assets/help/' + example)
    for path in expected:
        assert (QML / path).is_file()
        assert 'src/qt_dicom_viewer/qml/' + path in resources
    for size in (18, 36):
        image = render_icon('manual', '#aabcc8', 'transparent', size, size)
        assert not image.isNull() and image.width() == size


def test_manual_search_and_reading_state(qt_app):
    controller = ManualTabController()
    assert controller.chapterId == 'quick-start'
    controller.selectChapter('measurement')
    controller.setScrollPosition(120)
    controller.setScrollPosition(float('nan'))
    assert controller.scrollPosition == 120
    controller.setSearch('控制点')
    ids = [c['id'] for group in controller.navigation for c in group['chapters']]
    assert 'measurement-edit' in ids
    controller.setSearch('no-such-manual-topic')
    assert controller.navigation == [] and controller.chapterId == 'measurement'
    controller.setSearch('')
    assert len(controller.navigation) == 8
    controller.selectChapter('measurement')
    assert controller.scrollPosition == 0
    controller.selectChapter('not-found')
    assert controller.chapterId == 'quick-start'


def test_manual_empty_workspace_singleton_mru_and_export(scene):
    window, app, warnings = scene
    ws = app.workspaceController
    book, settings = find(window, 'sidebarManual'), find(window, 'sidebarSettings')
    assert (book.width(), book.height()) == (28, 28)
    assert settings.mapToScene(QPointF()).x() - book.mapToScene(QPointF(book.width(), 0)).x() == 4
    assert find(window, 'sidebarSettingsFooter').height() == 36
    click(window, book)
    assert ws.activeTabType == 'manual' and ws.activeViewport is None
    assert ws.currentTabAllViewports == [] and len(ws.tabs) == 1
    assert not any(i.isVisible() and i.objectName() == 'rightPanel' for i in descendants(window.contentItem()))
    assert app.exportController.current_series() == []
    manual = ws.manualController
    click(window, find(window, 'sidebarManual'))
    assert ws.manualController is manual and len(ws.tabs) == 1
    ws.openSettings()
    ws.openPacs()
    ws.openManual('measurement')
    assert len(ws.tabs) == 3 and ws.manualController is manual
    ws.closeTab('workspace-settings')
    assert ws.activeTabType == 'manual'
    ws.closeTab('workspace-manual')
    assert ws.activeTabType == 'pacs' and ws.manualController is None
    ws.openManual()
    assert ws.manualController.chapterId == 'quick-start'
    ws.closeTab('workspace-pacs')
    ws.closeTab('workspace-manual')
    QTest.qWait(40)
    assert not ws.tabs and ws.activeViewport is None
    assert not warnings, warnings


def test_manual_search_scroll_restore_and_context_jump(scene):
    window, app, warnings = scene
    window.resize(1000, 600)
    ws = app.workspaceController
    ws.openManual('measurement')
    QTest.qWait(80)
    wait_until(lambda: not find(window, 'operationManual').property('restoring'))
    reading = find(window, 'manualReadingArea')
    assert reading.property('contentHeight') > reading.height() + 150
    reading.setProperty('contentY', 140)
    QTest.qWait(20)
    assert ws.manualController.scrollPosition == 140
    ws.openManual()
    assert reading.property('contentY') == 140
    ws.openPacs()
    QTest.qWait(40)
    ws.openManual()
    QTest.qWait(80)
    wait_until(lambda: not find(window, 'operationManual').property('restoring'))
    assert find(window, 'manualReadingArea').property('contentY') == 140
    ws.openManual('voi')
    QTest.qWait(80)
    assert find(window, 'manualReadingArea').property('contentY') == 0
    type_text(window, find(window, 'manualSearch'), 'ROI')
    assert ws.manualController.search == 'ROI'
    selected = find(window, 'manualChapter-measurement-roi')
    click(window, selected)
    assert ws.manualController.chapterId == 'measurement-roi'
    ws.openManual('quick-start')
    QTest.qWait(60)
    assert find(window, 'manualSearch').property('text') == ''
    assert not warnings, warnings


@pytest.mark.parametrize('size', [(1000, 600), (1400, 900)])
def test_manual_all_chapters_layout_and_examples(scene, size, tmp_path):
    window, app, warnings = scene
    window.resize(*size)
    ws = app.workspaceController
    ws.openManual()
    QTest.qWait(80)
    navigation = find(window, 'manualNavigation')
    reading = find(window, 'manualReadingArea')
    assert navigation.mapToScene(QPointF(navigation.width(), 0)).x() <= reading.mapToScene(QPointF()).x()
    for chapter in manual_content()['chapters']:
        ws.openManual(chapter['id'])
        QTest.qWait(35)
        assert find(window, 'manualChapterTitle').property('text') == chapter['title']
        assert reading.property('contentY') == 0
        assert reading.property('contentWidth') == reading.width()
        for item in (navigation, reading):
            point = item.mapToScene(QPointF(item.width(), item.height()))
            assert point.x() <= size[0] and point.y() <= size[1]
        if chapter.get('example') or chapter.get('examples'):
            assert find(window, 'manualExample').property('sourceSize').width() > 0
    ws.openManual('measurement')
    QTest.qWait(60)
    assert window.grabWindow().save(str(tmp_path / f'manual-{size[0]}.png'))
    assert not warnings, warnings


def test_manual_roundtrip_preserves_mpr_measurement_and_segmentation(sidebar_scene):
    from qt_dicom_viewer.model import TabType
    from test_dicom_tags import wait_until
    from test_measurement_qml import _scene, _mouse_drag
    from test_mpr_voi_qml import _owner, settle

    window, app, records, warnings = sidebar_scene
    window.resize(1400, 900)
    ws = app.workspaceController
    from qt_dicom_viewer.ui.workers.dicom_render_worker import DicomRenderWorker
    from qt_dicom_viewer.core.volume_manager import VolumeManager
    worker = DicomRenderWorker(app._series_catalog, VolumeManager())
    ws.renderRequested.disconnect(app.render_service.submit)
    ws.renderRequested.connect(worker.handleRenderRequest)
    worker.render_finished.connect(ws.handleRenderResult)
    worker.render_failed.connect(lambda failure: pytest.fail(str(failure.error)))
    ws.createTab(records[0].series_instance_uid, 'Synthetic MPR', TabType.MPR)
    tab_id, tab = ws.activeTabId, ws.activeTab
    wait_until(lambda: all(v._plane_geometry is not None for v in tab.viewports_by_id.values()))
    viewport = next(v for v in tab.viewports_by_id.values() if v.viewportType == 'axial')
    tab.activateViewport(viewport.viewportId)
    tab.toolController.activateTool('measure')
    tab.toolController.selectInteraction('measure:rect')
    QTest.qWait(80)
    layer = next(i for i in descendants(window.contentItem()) if i.objectName() == 'dicomPixelLayer' and _owner(i) is viewport)
    _mouse_drag(window, _scene(layer, 15, 18), _scene(layer, 30, 35))
    measurements = viewport.measurementController.measurementItems
    assert len(measurements) == 1
    click(window, find(window, 'measurementManualButton'))
    assert ws.activeTabType == 'manual' and ws.manualController.chapterId == 'measurement'
    ws.activateTabId(tab_id)
    QTest.qWait(80)
    assert viewport.measurementController.measurementItems == measurements
    tab.toolController.activateTool('segmentation')
    tab.voiController.begin(viewport, 28, 28, .1)
    tab.voiController.finish(viewport, 58, 58)
    settle(tab.voiController)
    ranges = [r.copy() for r in tab.voiController.records]
    assert ranges
    click(window, find(window, 'voiManualButton'))
    assert ws.activeTabType == 'manual' and ws.manualController.chapterId == 'segmentation'
    ws.closeTab('workspace-manual')
    QTest.qWait(80)
    assert ws.activeTabId == tab_id and ws.activeViewport is viewport
    assert tab.voiController.records == ranges
    assert viewport.measurementController.measurementItems == measurements
    assert any(i.objectName() == 'mprVoiOverlay' and i.isVisible() for i in descendants(window.contentItem()))
    assert not warnings, warnings


def test_manual_roundtrip_preserves_3d_controller_state(sidebar_scene, monkeypatch):
    from dataclasses import replace
    from qt_dicom_viewer.model import TabType
    from qt_dicom_viewer.ui.controller.viewport.volume_viewport_controller import VolumeViewportController
    from test_dicom_tags import wait_until

    # Native GPU rendering has separate smoke tests; this test exercises Loader
    # transitions and the retained controller without requiring a display server.
    monkeypatch.setattr(VolumeViewportController, 'ensureNativeView', lambda self: None)
    monkeypatch.setattr(VolumeViewportController, 'setNativeVisible', lambda self, visible: None)
    window, app, records, warnings = sidebar_scene
    ws = app.workspaceController
    ws.createTab(records[0].series_instance_uid, 'Synthetic 3D', TabType.THREE_D)
    tab_id, viewport = ws.activeTabId, ws.activeViewport
    wait_until(lambda: viewport.loadState == 'ready')
    viewport._set_state(replace(viewport.state, zoom=1.8, pan=(.1, -.2)))
    state, display = viewport.state, viewport.display_state
    ws.openManual('volume')
    QTest.qWait(60)
    assert ws.activeViewport is None
    ws.activateTabId(tab_id)
    QTest.qWait(60)
    assert ws.activeViewport is viewport and viewport.state == state and viewport.display_state == display
    assert find(window, 'volumeViewport').isVisible()
    assert not warnings, warnings
