"""Exercise the 4D playback controls through a real offscreen QML view."""

from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, QUrl, Qt
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest
from shiboken6 import delete

from qt_dicom_viewer.model import SeriesDisplayMeta, TabConfig, TabType
from qt_dicom_viewer.ui.controller.tab.tab_controller import TabController
from test_measurement_qml import _visual_children, qt_app


def _controller(tab_type: TabType = TabType.FOUR_D) -> TabController:
    meta = SeriesDisplayMeta(
        patient_name="4D Example",
        patient_id="P4D",
        study_description="Perfusion",
        series_description="Dynamic CT",
        modality="CT",
        series_uid="series-4d",
        phase_identifiers=(1, 2, 3, 4, 5, 6),
        supports_four_d=True,
    )
    return TabController(
        TabConfig("test-tab", tab_type.value, tab_type, (meta,))
    )


@pytest.fixture
def four_d_panel(qt_app):
    controller = _controller()
    view = QQuickView()
    from qt_dicom_viewer.ui.svg_icon_provider import SvgIconProvider
    view.engine().addImageProvider("navigation", SvgIconProvider())
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.resize(280, 760)
    warnings = []
    view.engine().warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    view.setInitialProperties({
        "toolController": controller.toolController,
        "toolVisible": True,
        "viewportController": controller.activeViewport,
        "tabController": controller,
    })
    source = (
        Path(__file__).resolve().parents[1]
        / "src/qt_dicom_viewer/qml/sections/RightPanel.qml"
    )
    view.setSource(QUrl.fromLocalFile(str(source)))
    assert view.status() == QQuickView.Ready, [
        error.toString() for error in view.errors()
    ]
    view.show()
    QTest.qWait(100)
    try:
        yield view, controller, warnings
    finally:
        controller.pausePlayback()
        view.hide()
        delete(view)


def _find(view: QQuickView, name: str):
    return next(
        item
        for item in _visual_children(view.rootObject())
        if item.objectName() == name and item.isVisible()
    )


def _click(view: QQuickView, item) -> None:
    center = item.mapToScene(
        QPointF(item.width() / 2, item.height() / 2)
    ).toPoint()
    QTest.mouseClick(view, Qt.LeftButton, Qt.NoModifier, center)
    QTest.qWait(40)


def test_play_tool_opens_secondary_panel_and_controls_playback(
    four_d_panel,
    tmp_path,
) -> None:
    view, controller, warnings = four_d_panel
    play_tool = _find(view, "primaryTool-play")
    window_tool = _find(view, "primaryTool-window")

    assert not any(
        item.objectName() == "fourDPlaybackPanel" and item.isVisible()
        for item in _visual_children(view.rootObject())
    )
    _click(view, play_tool)

    panel = _find(view, "fourDPlaybackPanel")
    play_button = _find(view, "phasePlaybackButton")

    assert controller.toolController.activePanel == "play"
    assert panel.mapToScene(QPointF()).y() > play_tool.mapToScene(QPointF()).y()
    assert play_button.width() <= 34
    assert not play_button.property("checked")
    _click(view, play_button)
    assert controller.playing
    assert play_button.property("checked")
    assert play_tool.property("enabled")
    assert not window_tool.property("enabled")
    _click(view, window_tool)
    assert controller.toolController.activePanel == "play"
    _click(view, play_button)
    assert not controller.playing
    assert window_tool.property("enabled")

    screenshot = view.grabWindow()
    assert not screenshot.isNull()
    output = tmp_path / "four-d-panel.png"
    assert screenshot.save(str(output))
    print(f"QML preview: {output}")
    assert not warnings, warnings


def test_four_d_panel_updates_fps_and_accepts_phase_click(
    four_d_panel,
) -> None:
    view, controller, warnings = four_d_panel
    _click(view, _find(view, "primaryTool-play"))
    fps_slider = _find(view, "fpsSlider")
    fps_value = _find(view, "fpsValue")
    first_phase_button = _find(view, "phaseButton-0")
    phase_button = _find(view, "phaseButton-1")
    fifth_phase_button = _find(view, "phaseButton-4")
    sixth_phase_button = _find(view, "phaseButton-5")

    assert fps_slider.property("from") == 1.0
    assert fps_slider.property("to") == 15.0
    assert fps_slider.property("value") == 2.0
    controller.setFps(13)
    QTest.qWait(20)
    assert fps_slider.property("value") == 13.0
    assert fps_value.property("text") == "13"
    assert first_phase_button.property("checked")
    assert fifth_phase_button.mapToScene(QPointF()).y() == pytest.approx(
        first_phase_button.mapToScene(QPointF()).y()
    )
    assert sixth_phase_button.mapToScene(QPointF()).y() > (
        first_phase_button.mapToScene(QPointF()).y()
    )

    _click(view, phase_button)
    assert controller._pending_phase_index == 1
    assert not warnings, warnings


def test_non_four_d_right_panel_does_not_show_playback_controls(qt_app) -> None:
    controller = _controller(TabType.MPR)
    view = QQuickView()
    from qt_dicom_viewer.ui.svg_icon_provider import SvgIconProvider
    view.engine().addImageProvider("navigation", SvgIconProvider())
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.resize(280, 640)
    warnings = []
    view.engine().warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    view.setInitialProperties({
        "toolController": controller.toolController,
        "toolVisible": True,
        "viewportController": controller.activeViewport,
        "tabController": controller,
    })
    source = (
        Path(__file__).resolve().parents[1]
        / "src/qt_dicom_viewer/qml/sections/RightPanel.qml"
    )
    view.setSource(QUrl.fromLocalFile(str(source)))
    assert view.status() == QQuickView.Ready
    view.show()
    QTest.qWait(40)
    try:
        assert not any(
            item.objectName() == "primaryTool-play" and item.isVisible()
            for item in _visual_children(view.rootObject())
        )
        assert not any(
            item.objectName() == "fourDPlaybackPanel" and item.isVisible()
            for item in _visual_children(view.rootObject())
        )
        assert not warnings, warnings
    finally:
        view.hide()
        delete(view)
