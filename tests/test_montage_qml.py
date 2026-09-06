from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_montage_entry_and_center_loader_are_wired() -> None:
    left_panel = _read("src/qt_dicom_viewer/qml/sections/LeftPanel.qml")
    center_panel = _read(
        "src/qt_dicom_viewer/qml/sections/center/CenterPanel.qml"
    )

    assert 'shortLabel: "平铺"' in left_panel
    assert 'type: "montage"' in left_panel
    assert 'actionData.type !== "montage" || !leftPanel.panelController.scanning' in left_panel
    assert 'activeTabType === "montage"' in center_panel
    assert "ViewportSection.MontageViewport" in center_panel


def test_montage_qml_exposes_grid_controls_and_navigation() -> None:
    qml = _read(
        "src/qt_dicom_viewer/qml/sections/center/viewportArea/MontageViewport.qml"
    )

    assert "model: [2, 3, 4, 5, 6]" in qml
    assert "setVisibleRange(first, last)" in qml
    assert "openSlice(" in qml
    assert 'objectName: "montageWheelArea"' in qml
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
    qrc = _read("QtDicomViewer.qrc")
    assert (
        "src/qt_dicom_viewer/qml/sections/center/viewportArea/"
        "MontageViewport.qml"
    ) in qrc
