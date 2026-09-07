"""Exercise Montage scrolling through a real Qt wheel event."""

import os
from dataclasses import replace
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QPoint, QPointF, QUrl, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from shiboken6 import delete

from qt_dicom_viewer.model import WindowLevel
from test_montage_controller import _controller


@pytest.fixture(scope="module")
def qt_app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    app = QApplication.instance() or QApplication([])
    yield app


def test_montage_grid_scrolls_on_wheel_event(qt_app, tmp_path) -> None:
    controller = _controller(320)
    controller._baseline_window = WindowLevel(center=40.0, width=400.0)
    controller._state = replace(
        controller.viewport_state,
        window=controller._baseline_window,
    )
    opened: list[tuple] = []
    controller.sliceOpenRequested.connect(
        lambda *args: opened.append(args)
    )
    view = QQuickView()
    from qt_dicom_viewer.ui.svg_icon_provider import SvgIconProvider
    view.engine().addImageProvider("navigation", SvgIconProvider())
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.resize(1000, 720)
    warnings: list[str] = []
    view.engine().warnings.connect(
        lambda errors: warnings.extend(
            error.toString() for error in errors
        )
    )
    view.setInitialProperties({"viewportController": controller})
    source = (
        Path(__file__).resolve().parents[1]
        / "src/qt_dicom_viewer/qml/sections/center/viewportArea/"
        / "MontageViewport.qml"
    )
    view.setSource(QUrl.fromLocalFile(str(source)))
    assert view.status() == QQuickView.Ready, [
        error.toString() for error in view.errors()
    ]
    view.show()
    QTest.qWait(100)

    try:
        root = view.rootObject()
        grid = root.findChild(QQuickItem, "montageGrid")
        assert grid is not None
        assert grid.property("contentHeight") > grid.height()

        first_tile_center = grid.mapToScene(
            QPointF(
                float(grid.property("cellWidth")) / 2,
                float(grid.property("cellHeight")) / 2,
            )
        )
        QTest.mouseClick(
            view,
            Qt.LeftButton,
            Qt.NoModifier,
            first_tile_center.toPoint(),
        )
        QTest.qWait(40)
        assert opened and opened[0][1] == 0

        before = float(grid.property("contentY"))

        local_position = grid.mapToScene(
            QPointF(grid.width() / 2, grid.height() / 2)
        )
        global_position = view.mapToGlobal(local_position.toPoint())
        event = QWheelEvent(
            local_position,
            QPointF(global_position),
            QPoint(),
            QPoint(0, -120),
            Qt.NoButton,
            Qt.NoModifier,
            Qt.ScrollUpdate,
            False,
        )
        QCoreApplication.sendEvent(view, event)
        QTest.qWait(80)

        assert float(grid.property("contentY")) > before
        assert not warnings, warnings

        screenshot = view.grabWindow()
        if not screenshot.isNull():
            output = tmp_path / "montage-scroll.png"
            assert screenshot.save(str(output))
            print(f"QML preview: {output}")
    finally:
        view.hide()
        delete(view)
