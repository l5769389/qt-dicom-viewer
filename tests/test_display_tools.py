from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest
from PySide6.QtCore import QSize

from qt_dicom_viewer.core.pseudocolor import (
    COLOR_MAP_SPECS,
    apply_color_map,
    color_map_options,
)
from qt_dicom_viewer.model import ToolType, ViewportDisplaySettings
from qt_dicom_viewer.ui.controller.viewport.controller.text_annotation_controller import (
    TextAnnotationController,
)
from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
from test_viewport_transform import _controller, _render_result


def test_all_reference_color_maps_have_renderable_luts() -> None:
    pixels = np.array([[0, 64, 128, 255]], dtype=np.uint8)
    options = color_map_options()

    assert [option["label"] for option in options[:8]] == [
        "BW", "BWInverse", "BlackBody", "Cardiac",
        "Flow", "French", "GrayRainbow", "HotGreen",
    ]
    assert {option["colorMap"] for option in options} == set(COLOR_MAP_SPECS)

    for option in options:
        rendered = apply_color_map(pixels, option["colorMap"])
        expected_shape = pixels.shape if option["colorMap"].startswith("grayscale") else (1, 4, 3)
        assert rendered.shape == expected_shape
        assert rendered.dtype == np.uint8
        assert option["stops"][0]["position"] == 0.0
        assert option["stops"][-1]["position"] == 1.0

    assert np.array_equal(apply_color_map(pixels, "grayscale"), pixels)
    assert np.array_equal(
        apply_color_map(pixels, "grayscale-inverted"),
        255 - pixels,
    )
    with pytest.raises(ValueError, match="Unknown color map"):
        apply_color_map(pixels, "missing")


def test_image_provider_accepts_rgb_pseudocolor() -> None:
    provider = DicomImageProvider()
    rgb = np.zeros((3, 5, 3), dtype=np.uint8)
    rgb[:, :, 1] = 127
    provider.set_array("viewport", rgb)

    size = QSize()
    image = provider.requestImage("viewport/1", size, QSize())

    assert (size.width(), size.height()) == (5, 3)
    assert image.width() == 5
    assert image.height() == 3
    assert image.pixelColor(0, 0).green() == 127


def test_text_annotations_are_slice_scoped_and_editable() -> None:
    controller = TextAnnotationController()
    viewport = _controller()
    frame = replace(_render_result(viewport).frame_meta, slice_index=2)
    controller.set_frame("series-1", frame)
    controller.setAnnotationText("病灶 A")
    controller.setAnnotationColor("#66d0ff")
    controller.setAnnotationFontSize(24)
    controller.addAnnotation(12.5, 30.25)

    assert len(controller.annotationItems) == 1
    item = controller.annotationItems[0]
    assert item["text"] == "病灶 A"
    assert item["color"] == "#66d0ff"
    assert item["fontSize"] == 24
    assert controller.hasSelection

    controller.setAnnotationText("已编辑")
    assert controller.annotationItems[0]["text"] == "已编辑"

    controller.set_current_slice(3)
    assert controller.annotationItems == []
    assert not controller.hasSelection
    controller.set_current_slice(2)
    assert controller.annotationItems[0]["text"] == "已编辑"

    shifted = replace(
        frame,
        geometry=replace(
            frame.geometry,
            image_position_patient=(1.0, 0.0, 0.0),
        ),
    )
    controller.set_frame("series-1", shifted)
    assert controller.annotationItems == []
    controller.set_frame("series-1", frame)
    assert controller.annotationItems[0]["text"] == "已编辑"

    controller.selectAnnotation(item["annotationId"])
    controller.deleteSelected()
    assert controller.annotationItems == []


def test_viewport_applies_color_map_settings_and_annotation_reset() -> None:
    viewport = _controller()
    viewport.handleRenderResult(_render_result(viewport))
    requests = []
    viewport.renderRequested.connect(requests.append)

    viewport.applyColorMap("blackbody")
    assert viewport.activeColorMap == "blackbody"
    assert requests[-1].color_map == "blackbody"
    assert len(viewport.activeColorMapStops) >= 2

    viewport.setViewportSetting("window-annotations", False)
    viewport.setViewportSetting("hide-sensitive-info", True)
    viewport.setViewportSetting("scale-bar", True)
    viewport.setViewportSetting("color-bar", True)
    viewport.setViewportSetting("dicom-overlay", False)
    viewport.setViewportSetting("localizer", False)
    viewport.setViewportSetting("fit-to-window", False)
    assert not viewport.showWindowAnnotations
    assert viewport.hideSensitiveInfo
    assert viewport.showScaleBar
    assert viewport.showColorBar
    assert not viewport.showDicomOverlay
    assert not viewport.showLocalizer
    assert not viewport.fitToWindow

    tools = viewport._tool_controller
    tools.activateTool("annotate")
    viewport.textAnnotationController.setAnnotationText("重点")
    viewport.selectMeasurementAt(True, 20, 25, 8, 6, 50, 60)
    assert len(viewport.textAnnotationController.annotationItems) == 1

    viewport.reset_tool_state(ToolType.ANNOTATE)
    assert viewport.textAnnotationController.annotationItems == []
    viewport.reset_tool_state(ToolType.PSEUDOCOLOR)
    assert viewport.activeColorMap == "grayscale"
    viewport.reset_tool_state(ToolType.VIEWPORT_SETTINGS)
    assert viewport.viewport_state.display_settings == ViewportDisplaySettings()
