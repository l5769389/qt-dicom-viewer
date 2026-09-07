from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from shiboken6 import delete

from qt_dicom_viewer.ui.app_controller import AppController
from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
from test_dicom_tags import qt_app, wait_until
from test_pacs import pacs_server, STUDY, SERIES
from test_tag_qml import descendants, find, click, type_text


@pytest.fixture
def scene(qt_app, tmp_path):
    provider = DicomImageProvider()
    controller = AppController(provider, pacs_config_path=tmp_path / "pacs.json", pacs_import_root=tmp_path / "imports")
    engine = QQmlApplicationEngine()
    from qt_dicom_viewer.ui.svg_icon_provider import SvgIconProvider
    engine.addImageProvider("navigation", SvgIconProvider())
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    engine.addImageProvider("dicom", provider)
    engine.rootContext().setContextProperty("appController", controller)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).resolve().parents[1] / "src/qt_dicom_viewer/qml/Main.qml")))
    assert engine.rootObjects(), warnings
    window = engine.rootObjects()[0]
    QTest.qWait(50)
    try:
        yield window, controller, warnings
    finally:
        window.hide()
        controller.shutdown()
        delete(engine)


def test_ui_configure_test_save_query_and_import(scene, pacs_server, tmp_path):
    window, app, warnings = scene
    pacs, workspace = app.pacsController, app.workspaceController
    assert find(window, "homeOpenPacs").isEnabled()
    click(window, find(window, "sidebarSettings"))
    assert workspace.activeTabType == "settings"
    click(window, find(window, "sidebarSettings"))
    assert len(workspace.tabs) == 1
    click(window, find(window, "pacsAddProfile"))
    QTest.qWait(100)
    type_text(window, find(window, "pacsProfileName"), "Orthanc Local")
    type_text(window, find(window, "pacsProfileUrl"), pacs_server.url)
    click(window, find(window, "pacsTestDraft"))
    wait_until(lambda: not pacs.busy)
    assert "连接成功" in pacs.message
    assert not pacs.profiles  # Testing a draft does not save it.
    click(window, find(window, "pacsSaveProfile"))
    QTest.qWait(100)
    assert len(pacs.profiles) == 1 and pacs.defaultName == "Orthanc Local"
    screenshot(window, tmp_path, "settings")
    click(window, find(window, "sidebarPacs"))
    assert workspace.activeTabType == "pacs"
    click(window, find(window, "pacsQueryStudies"))
    wait_until(lambda: not pacs.busy)
    click(window, find(window, "pacsStudy-" + STUDY))
    wait_until(lambda: not pacs.busy)
    click(window, find(window, "pacsSeries-" + SERIES))
    assert pacs.selectedCount == 1
    screenshot(window, tmp_path, "browser")
    for width, height in [(1000, 600), (1400, 760)]:
        window.resize(width, height)
        QTest.qWait(80)
        for name in ("pacsQueryStudies", "pacsStudiesList", "pacsSeriesList", "pacsImportSelected"):
            control = find(window, name)
            p1 = control.mapToScene(QPointF(0, 0))
            p2 = control.mapToScene(QPointF(control.width(), control.height()))
            assert 0 <= p1.x() < p2.x() <= width
            assert 0 <= p1.y() < p2.y() <= height
        screenshot(window, tmp_path, f"browser-{width}")
    click(window, find(window, "pacsImportSelected"))
    wait_until(lambda: not pacs.busy)
    assert not pacs.isError, pacs.message
    assert workspace.activeTabType == "2d"
    assert len(app.panelController.seriesItems) == 1
    assert app.panelController.activeSeriesUid == SERIES
    assert app._series_catalog.get_series(SERIES).dicom_file_count == 3
    # Settings and PACS are real tabs and do not create/render image viewports.
    click(window, find(window, "sidebarSettings"))
    assert workspace.activeViewport is None and workspace.currentTabAllViewports == []
    assert not any(item.objectName() == "rightPanel" and item.isVisible() for item in descendants(window.contentItem()))
    window.resize(1000, 600)
    QTest.qWait(80)
    screenshot(window, tmp_path, "settings-1000")
    workspace.closeTab("workspace-settings")
    workspace.closeTab("workspace-pacs")
    QTest.qWait(80)
    assert workspace.activeTabType == "2d"
    assert not warnings, warnings


def screenshot(window, tmp_path, name):
    QTest.qWait(50)
    shot = window.grabWindow()
    assert not shot.isNull()
    assert shot.save(str(tmp_path / (name + ".png")))
    assert shot.save("/private/tmp/pacs-" + name + ".png")


def test_sources_visibility_and_unconfigured_home(scene):
    window, app, warnings = scene
    click(window, find(window, "homeOpenPacs"))
    click(window, find(window, "pacsConfigureEmpty"))
    assert app.workspaceController.activeTabType == "settings"
    click(window, find(window, "enablePacsSource"))
    assert not app.pacsController.pacsEnabled
    assert not any(item.objectName() == "sidebarPacs" and item.isVisible() for item in descendants(window.contentItem()))
    click(window, find(window, "enableLocalSource"))
    assert app.pacsController.localEnabled  # Last source cannot be disabled.
    assert find(window, "enableLocalSource").property("checked") is True
    click(window, find(window, "enablePacsSource"))
    click(window, find(window, "enableLocalSource"))
    assert not app.pacsController.localEnabled and app.pacsController.pacsEnabled
    assert not any(item.objectName() == "sidebarOpenFolder" and item.isVisible() for item in descendants(window.contentItem()))
    assert not warnings, warnings


def test_series_selection_and_status_updates_preserve_scroll(scene, pacs_server):
    from PySide6.QtCore import QMetaObject, Q_ARG
    from test_pacs import element
    window, app, warnings = scene
    pacs = app.pacsController
    pacs_server.series_rows = [{"0020000E": element("UI", SERIES + f".{i}"),
                               "0008103E": element("LO", f"Series {i}"),
                               "00080060": element("CS", "CT"),
                               "00200011": element("IS", i),
                               "00201209": element("IS", 3)} for i in range(30)]
    pacs.saveProfile({"name": "PACS", "url": pacs_server.url})
    app.workspaceController.openPacs()
    pacs.queryStudies({}, 50)
    wait_until(lambda: not pacs.busy)
    pacs.selectStudy(STUDY)
    wait_until(lambda: not pacs.busy)
    QTest.qWait(50)
    view = find(window, "pacsSeriesList")
    QMetaObject.invokeMethod(view, "positionViewAtIndex", Q_ARG(int, 25), Q_ARG(int, 1))
    QTest.qWait(50)
    before = view.property("contentY")
    assert before > 1000
    click(window, find(window, "pacsSeries-" + SERIES + ".25"))
    assert pacs.selectedCount == 1
    assert view.property("contentY") == pytest.approx(before)
    pacs.testProfile(pacs.selectedProfileId)
    wait_until(lambda: not pacs.busy)
    assert view.property("contentY") == pytest.approx(before)
    assert not warnings, warnings
