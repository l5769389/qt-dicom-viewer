"""Mouse feedback on real navigation and viewport controls, without layout shifts."""
import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from test_dicom_tags import qt_app
from test_tag_qml import scene as navigation_scene, find, click
from test_display_tools_qml import display_panel, _find, _click, _visual_children


def feedback(window, button, *, disabled=False):
    outside = QPoint(2, window.height() - 2)
    point = button.mapToScene(QPointF(button.width() / 2, button.height() / 2)).toPoint()
    bounds = (button.mapToScene(QPointF()), button.width(), button.height())
    background = button.property("background")
    QTest.mouseMove(window, outside)
    QTest.qWait(120)
    idle = background.property("color")
    QTest.mouseMove(window, point)
    QTest.qWait(120)
    hover = background.property("color")
    QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, point)
    QTest.qWait(120)
    pressed = background.property("color")
    if disabled:
        assert idle == hover == pressed
        assert not button.property("down")
    else:
        assert button.property("hovered") and button.property("down")
        assert len({c.name(c.NameFormat.HexArgb) for c in (idle, hover, pressed)}) == 3
    # Release outside cancels the command; it must restore the previous state.
    QTest.mouseMove(window, outside)
    QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, outside)
    QTest.qWait(120)
    assert not button.property("down")
    assert background.property("color") == idle
    assert bounds == (button.mapToScene(QPointF()), button.width(), button.height())


def test_view_navigation_feedback_and_disabled_state(navigation_scene):
    window, workspace, series, warnings = navigation_scene
    feedback(window, find(window, "openView-2d"), disabled=True)
    click(window, find(window, "series-" + series.series_instance_uid))
    for name in ("openView-2d", "openView-mpr", "openView-3d", "openView-montage"):
        feedback(window, find(window, name))
    assert not workspace.tabs  # Canceled presses must not open any view.
    click(window, find(window, "openView-2d"))
    feedback(window, find(window, "openView-2d"))
    assert workspace.activeTabType == "2d" and len(workspace.tabs) == 1
    assert not warnings, "\n".join(warnings)


def test_primary_and_secondary_tools_feedback(display_panel, tmp_path):
    view, controller, warnings = display_panel
    root = view.rootObject()
    for name in ("primaryTool-pan", "primaryTool-zoom", "primaryTool-reset"):
        feedback(view, _find(root, name))
    _click(view, _find(root, "primaryTool-pan"))
    feedback(view, _find(root, "primaryTool-pan"))
    assert controller._tool_controller.activeTool == "pan"
    _click(view, _find(root, "primaryTool-window"))
    preset = next(i for i in _visual_children(root)
                  if i.objectName().startswith("windowPreset-") and i.isVisible())
    feedback(view, preset)
    _click(view, preset)
    feedback(view, preset)
    _click(view, _find(root, "primaryTool-pseudocolor"))
    feedback(view, _find(root, "colorMap-blackbody"))
    _click(view, _find(root, "colorMap-blackbody"))
    feedback(view, _find(root, "colorMap-blackbody"))
    assert controller.activeColorMap == "blackbody"
    assert view.grabWindow().save(str(tmp_path / "button-feedback.png"))
    assert not warnings, "\n".join(warnings)
