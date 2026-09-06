"""QML menus can be verified without constructing a native VTK window."""
from dataclasses import replace
from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, QUrl, Qt
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest
from shiboken6 import delete

from qt_dicom_viewer.core.volume_view import VolumeViewState
from test_measurement_qml import _visual_children, qt_app
from test_volume_display import loaded_tab, volume
from test_volume_edit import draw, wait_edit


@pytest.fixture
def panel(qt_app, loaded_tab, request):
    controller = loaded_tab.activeViewport
    if getattr(request, "param", "CT") == "MR":
        controller.viewport_config = replace(controller.viewport_config,
            series_meta=replace(controller.viewport_config.series_meta, modality="MR"))
    view = QQuickView()
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.resize(250, 700)
    warnings = []
    view.engine().warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    view.setInitialProperties(dict(toolController=loaded_tab.toolController,
        viewportController=controller, toolVisible=True))
    path = Path(__file__).resolve().parents[1]/"src/qt_dicom_viewer/qml/sections/RightPanel.qml"
    view.setSource(QUrl.fromLocalFile(str(path)))
    assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
    view.show()
    QTest.qWait(60)
    try:
        yield view, controller, loaded_tab.toolController, warnings
    finally:
        view.hide()
        delete(view)


def find(view, name):
    return next(item for item in _visual_children(view.rootObject())
                if item.objectName() == name and item.isVisible())


def click(view, name):
    item = find(view, name)
    point = item.mapToScene(QPointF(item.width()/2, item.height()/2)).toPoint()
    QTest.mouseClick(view, Qt.LeftButton, pos=point)
    QTest.qWait(20)


def test_direction_menu_clicks_and_rotation_update_one_badge(panel, tmp_path):
    view, controller, tools, warnings = panel
    assert find(view, "currentVolumeFace").property("text") == "A"
    click(view, "primaryTool-volume-direction")
    assert tools.activeInteraction == "volume:rotate"
    for face in "APLRSI":
        click(view, "volumeFace-"+face)
        assert controller.currentFace == face
        assert find(view, "currentVolumeFace").property("text") == face
        assert sum(find(view, "volumeFace-"+f).property("checked") for f in "APLRSI") == 1
    click(view, "volumeFace-A")
    controller.begin_drag((300, 300), (600, 600))
    controller.update_drag((550, 310))
    controller.end_drag()
    QTest.qWait(20)
    assert controller.currentFace != "A"
    assert find(view, "currentVolumeFace").property("text") == controller.currentFace
    assert find(view, "volumeFace-"+controller.currentFace).property("checked")
    click(view, "activeToolReset")
    assert controller.state == VolumeViewState()
    assert find(view, "currentVolumeFace").property("text") == "A"
    assert view.grabWindow().save(str(tmp_path/"volume-directions-panel.png"))
    assert not warnings, warnings


def test_grouped_templates_and_drag_only_window_tool(panel, tmp_path):
    view, controller, tools, warnings = panel
    click(view, "primaryTool-volume-preset")
    assert tools.activeInteraction == "volume:rotate"
    labels = {item.property("text") for item in _visual_children(view.rootObject())
              if item.isVisible() and item.property("text")}
    assert {"General", "CT", "CTA"} <= labels
    for preset in ("general", "bone", "lung", "vessel", "mip", "xray"):
        click(view, "volumePreset-"+preset)
        assert controller.currentPresetId == preset
        assert find(view, "volumePreset-"+preset).property("checked")
    click(view, "volumePreset-bone")
    assert view.grabWindow().save(str(tmp_path/"volume-presets-panel.png"))
    click(view, "primaryTool-window")
    assert tools.activePanel == "" and tools.activeInteraction == "window"
    labels = {item.property("text") for item in _visual_children(view.rootObject()) if item.isVisible()}
    assert "WL" not in labels and "WW" not in labels and "预设" not in labels
    assert not any(item.metaObject().className().startswith("QQuickTextInput")
                   for item in _visual_children(view.rootObject()) if item.isVisible())
    assert not warnings, warnings


@pytest.mark.parametrize("panel", ["MR"], indirect=True)
def test_ct_templates_are_disabled_in_mr_panel(panel):
    view, controller, tools, warnings = panel
    click(view, "primaryTool-volume-preset")
    for preset in ("bone", "lung", "vessel"):
        assert not find(view, "volumePreset-"+preset).isEnabled()
        click(view, "volumePreset-"+preset)
        assert controller.currentPresetId == "general"
    for preset in ("mip", "xray"):
        assert find(view, "volumePreset-"+preset).isEnabled()
        click(view, "volumePreset-"+preset)
        assert controller.currentPresetId == preset
    assert not warnings, warnings


def test_freehand_crop_actions_and_bottom_reset(panel, qt_app, tmp_path):
    view, controller, tools, warnings = panel
    click(view, "primaryTool-volume-crop")
    assert tools.activePanel == "volume-crop" and tools.activeInteraction == "volume:crop"
    assert not find(view, "volumeCrop-inside").isEnabled()
    assert not find(view, "volumeCrop-outside").isEnabled()
    draw(controller)
    qt_app.processEvents()
    assert find(view, "volumeCrop-inside").isEnabled()
    assert find(view, "volumeCrop-outside").isEnabled()
    assert view.grabWindow().save(str(tmp_path/"volume-crop-panel.png"))
    click(view, "volumeCrop-outside")
    wait_edit(qt_app, controller)
    assert controller.hasCrop and not controller.hasCropSelection
    click(view, "activeToolReset")
    assert not controller.hasCrop
    draw(controller)
    qt_app.processEvents()
    click(view, "volumeCrop-clear")
    assert not controller.hasCropSelection
    assert not warnings, warnings


@pytest.mark.parametrize("panel", ["MR"], indirect=True)
def test_bed_toggle_is_disabled_for_non_ct(panel):
    view, controller, tools, warnings = panel
    assert not find(view, "primaryTool-volume-bed").isEnabled()
    assert not warnings, warnings
