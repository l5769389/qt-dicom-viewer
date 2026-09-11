from pathlib import Path

from test_dicom_tags import qt_app
from test_series_sidebar import sidebar_scene
from test_tag_qml import find, click


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_montage_entry_and_center_loader_are_wired(sidebar_scene) -> None:
    window, app, records, warnings = sidebar_scene
    click(window, find(window, "series-" + records[0].series_instance_uid))
    button = find(window, "openView-montage")
    assert button.isEnabled()
    assert button.parentItem().property("tooltipText") == "平铺视图"
    click(window, button)
    assert app.workspaceController.activeTabType == "montage"
    assert find(window, "montageGrid").isVisible()
    assert not warnings, warnings


def test_montage_qml_exposes_grid_controls_and_navigation() -> None:
    qml = _read(
        "src/qt_dicom_viewer/qml/sections/center/viewportArea/MontageViewport.qml"
    )

    assert "model: [2, 3, 4, 5, 6]" in qml
    assert "setVisibleRange(first, last)" in qml
    assert "openSlice(" in qml
    assert 'objectName: "montageWheelHandler"' in qml
    assert "onWheel: wheelEvent =>" in qml
    assert "montageGrid.contentY = Math.max" in qml
    assert 'tile.loadState === "error"' in qml
    for tag_label in (
        "患者姓名",
        "患者 ID / 性别 / 年龄",
        "检查 / 序列描述",
        "扫描参数",
        "采集日期 / 时间",
        "层厚",
    ):
        assert tag_label in qml


def test_montage_tab_badge_is_responsive() -> None:
    tab_bar = _read(
        "src/qt_dicom_viewer/qml/sections/center/TabBarSection.qml"
    )

    assert "tabTypeLabel.implicitWidth + 12" in tab_bar
    # Pseudocolor is checked with rendered pixels in test_settings_redesign.py.


def test_montage_qml_is_in_the_compiled_resource_manifest() -> None:
    qrc = _read("Voxenra.qrc")
    assert (
        "src/qt_dicom_viewer/qml/sections/center/viewportArea/"
        "MontageViewport.qml"
    ) in qrc
