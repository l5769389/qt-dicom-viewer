from pathlib import Path
from dataclasses import replace
import time

import numpy as np
import pytest
from PySide6.QtCore import QUrl, Qt, QPointF, QMetaObject, QObject
from PySide6.QtQuick import QQuickView, QQuickWindow
from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest
from shiboken6 import delete

from test_measurement_qml import qt_app, _visual_children, _scene, _mouse_drag
from test_pet_fusion import paired_series
from qt_dicom_viewer.ui.controller.workspace_controller import WorkspaceController
from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
from qt_dicom_viewer.ui.workers.dicom_render_worker import DicomRenderWorker
from qt_dicom_viewer.core.volume_manager import VolumeManager
from qt_dicom_viewer.core.mpr_voi import evaluate_voi


def settle(controller):
    deadline = time.monotonic() + 5
    while controller.busy and not controller.error and time.monotonic() < deadline:
        QTest.qWait(20)
    assert not controller.error
    assert not controller.busy
    QTest.qWait(30)


@pytest.mark.parametrize("modality", ["CT", "PT"])
def test_real_mpr_draw_edit_threshold_depth_and_voi(qt_app, paired_series, tmp_path, modality):
    catalog, ct, pet = paired_series
    series = ct if modality == "CT" else pet
    provider = DicomImageProvider()
    workspace = WorkspaceController(catalog, provider)
    worker = DicomRenderWorker(catalog, VolumeManager())
    worker.render_finished.connect(workspace.handleRenderResult)
    worker.render_failed.connect(lambda failure: pytest.fail(str(failure.error)))
    workspace.renderRequested.connect(worker.handleRenderRequest)
    workspace.createTab(series.series_instance_uid, "MPR VOI", "mpr")
    tab = next(iter(workspace._tab_dict.values()))
    controller = tab.voiController
    tab.toolController.activateTool("segmentation")
    view = QQuickView()
    from qt_dicom_viewer.ui.svg_icon_provider import SvgIconProvider
    view.engine().addImageProvider("navigation", SvgIconProvider())
    view.engine().addImageProvider("dicom", provider)
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.resize(1550, 1100)
    warnings = []
    view.engine().warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    view.setInitialProperties({"workspace": workspace, "tabController": tab})
    view.setSource(QUrl.fromLocalFile(str(Path(__file__).parent / "qml/MprVoiWorkspace.qml")))
    assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
    view.show()
    QTest.qWait(80)
    try:
        items = list(_visual_children(view.rootObject()))
        assert any(x.objectName() == "mprVoiPanel" and x.isVisible() for x in items)
        layers = [x for x in items if x.objectName() == "dicomPixelLayer"]
        viewport = next(v for v in tab.viewports_by_id.values() if v.viewportType == "axial")
        # Locate its visual layer by walking from Viewport's controller property.
        layer = next(x for x in layers if _owner(x) is viewport)
        g = viewport._plane_geometry
        center = np.array([(g.columns-1)/2, (g.rows-1)/2])
        # Starts on crosshair lines: VOI drawing must take priority over rotation.
        start, end = center - 1.2, center + 1.2
        _mouse_drag(view, _scene(layer, *start), _scene(layer, *end))
        settle(controller)
        assert len(controller.records) == 1
        key = controller.selectedId
        r = controller.records[0]
        assert r["depthAuto"]
        assert r["region"].size[2] == pytest.approx(np.sqrt(np.prod(r["region"].size[:2])))
        assert controller.evaluations[key].metrics["count"] > 0
        assert all(v.voiOverlays for v in tab.viewports_by_id.values() if hasattr(v, "voiOverlays"))

        # Narrow panels keep mode buttons and numeric fields on separate rows.
        for width in (260, 300, 390):
            view.rootObject().setProperty("rightPanelWidth", width)
            QTest.qWait(30)
            visual = {x.objectName(): x for x in _visual_children(view.rootObject()) if x.objectName()}
            label = visual["voiThresholdLabel"]
            absolute = visual["voiThresholdAbsolute"]
            percent = visual["voiThresholdPercent"]
            assert label.x() + label.width() <= absolute.x()
            assert absolute.x() + absolute.width() <= percent.x()
            field = visual["voiThreshold"]
            mode_row = visual["voiThresholdModeRow"]
            assert mode_row.y() + mode_row.height() <= field.y()
            assert field.width() > 180

        # Exercise actual number entry and slider-driven scheduling.
        depth = next(x for x in _visual_children(view.rootObject()) if x.objectName() == "voiDepth")
        depth.forceActiveFocus()
        QMetaObject.invokeMethod(depth, "selectAll")
        QTest.keyClick(view, "6")
        QTest.keyClick(view, Qt.Key_Return)
        settle(controller)
        assert controller.records[0]["region"].size[2] == 6
        assert not r["depthAuto"]
        auto = next(x for x in _visual_children(view.rootObject()) if x.objectName() == "voiAutoDepth")
        _click(view, auto)
        settle(controller)
        assert r["depthAuto"]
        threshold = next(x for x in _visual_children(view.rootObject()) if x.objectName() == "voiThreshold")
        threshold.forceActiveFocus()
        QMetaObject.invokeMethod(threshold, "selectAll")
        for c in ("5" if modality == "PT" else "2500"):
            QTest.keyClick(view, c)
        QTest.keyClick(view, Qt.Key_Return)
        settle(controller)
        oracle = evaluate_voi(viewport._voi_volume, r["region"], threshold=r["threshold"])
        assert controller.evaluations[key].metrics == oracle.metrics
        controller.setThreshold(1e10)
        settle(controller)
        assert controller.evaluations[key].metrics["count"] == 0
        controller.setPercent(True)
        controller.setThreshold(50)
        settle(controller)
        assert controller.evaluations[key].metrics["count"] > 0

        if modality == "PT":
            controller.setUnit("kbqml")
            settle(controller)
            assert controller.selected["unit"] == "kBq/ml"
            # Display changes cannot silently relabel saved quantitative thresholds.
            viewport.setPetUnit("source")
            settle(controller)
            assert controller.selected["unit"] == "kBq/ml"

        before = r["region"]
        _mouse_drag(view, _scene(layer, *center), _scene(layer, *(center + [.2, .1])))
        settle(controller)
        assert not np.allclose(before.center, r["region"].center)
        assert len(controller.records) == 1
        controller.toggleVisible(key)
        assert viewport.voiOverlays == []
        controller.toggleVisible(key)
        controller.setEnabled(False)
        assert viewport.voiOverlays == []
        controller.setEnabled(True)
        tab.toolController.activateTool("voi")
        _mouse_drag(view, _scene(layer, *center), _scene(layer, *(center + [1, 0])))
        settle(controller)
        assert len(controller.records) == 2
        assert controller.records[-1]["kind"] == "voi"
        circle = controller.records[-1]
        assert circle["region"].shape == "ellipsoid"
        assert circle["region"].size[0] == circle["region"].size[1] == circle["region"].size[2]
        assert controller.evaluations[controller.selectedId].threshold is None
        interaction = next(x for x in _visual_children(view.rootObject())
                           if x.objectName() == "viewportInteractionLayer" and _owner(x) is viewport)
        QTest.mouseMove(view, _scene(layer, *center), 20)
        QTest.qWait(30)
        assert interaction.property("hoverCursorKind") == "pan"
        QTest.mouseMove(view, _scene(layer, *(center + [1, 0])), 20)
        QTest.qWait(30)
        assert interaction.property("hoverCursorKind") == "resize"
        # Editing stays a resize as it crosses a crosshair. No raster/icon reloads.
        QTest.mousePress(view, Qt.LeftButton, Qt.NoModifier, _scene(layer, *(center + [1, 0])))
        QTest.mouseMove(view, _scene(layer, *(center + [1.1, .1])), 20)
        QTest.qWait(30)
        assert interaction.property("effectiveCursorKind") == "resize"
        QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, _scene(layer, *(center + [1.1, .1])))
        settle(controller)
        controller.setEnabled(False)
        QTest.mouseMove(view, _scene(layer, *center), 20)
        QTest.qWait(30)
        assert interaction.property("hoverCursorKind") == "default"
        controller.setEnabled(True)
        # Rename in the list, without a second description field in the card.
        name = next(x for x in _visual_children(view.rootObject()) if x.objectName() == "voiSelect-" + circle["id"])
        QTest.mouseDClick(view, Qt.LeftButton, Qt.NoModifier, name.mapToScene(QPointF(name.width()/2, name.height()/2)).toPoint())
        QTest.qWait(30)
        name_field = next(x for x in _visual_children(view.rootObject()) if x.objectName() == "voiName-" + circle["id"])
        assert name_field.isVisible()
        for char in "Lesion A":
            QTest.keyClick(view, char)
        QTest.keyClick(view, Qt.Key_Return)
        assert circle["name"] == "Lesion A"

        # The manual is a separate ordinary window with its own surface,
        # navigation, resizing and keyboard shortcuts.
        help_button = next(x for x in _visual_children(view.rootObject()) if x.objectName() == "voiManualButton")
        QTest.qWait(40)
        before_manual = view.grabWindow()
        _click(view, help_button)
        manual = view.rootObject().findChild(QObject, "operationManual")
        assert manual.property("visible") and manual.property("chapter") == "voi"
        assert manual.property("category") == "mpr-segmentation"
        assert isinstance(manual, QQuickWindow) and manual is not view
        assert manual.modality() == Qt.NonModal
        assert manual.transientParent() is None
        assert manual.flags() & Qt.WindowType_Mask == Qt.Window
        # Opening the manual must not draw an overlay in the image viewport.
        assert before_manual.copy(12, 12, 1000, 900) == view.grabWindow().copy(12, 12, 1000, 900)
        main_size = view.size()
        records_before = [r.copy() for r in controller.records]
        # Directory stays on the left; only the right reading pane scrolls.
        for size in ((720, 560), (1060, 800)):
            manual.resize(*size)
            QTest.qWait(40)
            visual = {x.objectName(): x for x in _visual_children(manual.contentItem()) if x.objectName()}
            navigation, reading = visual["manualNavigation"], visual["voiManualReadingArea"]
            assert navigation.mapToScene(QPointF(navigation.width(), 0)).x() <= reading.mapToScene(QPointF(0, 0)).x()
            assert (manual.width(), manual.height()) == size
            assert view.size() == main_size
            assert reading.height() <= manual.height()
            button = visual["voiManualChapter-voi"]
            category = visual["manualCategory-mpr-segmentation"]
            assert button.mapToScene(QPointF(0, 0)).x() > category.mapToScene(QPointF(0, 0)).x()
            before_y = button.mapToScene(QPointF(0, 0)).y()
            reading.setProperty("contentY", 120)
            assert button.mapToScene(QPointF(0, 0)).y() == before_y
        for chapter in ("segmentation", "quantification", "interaction", "management", "voi"):
            name = "voiManualChapter-" + chapter
            button = next(x for x in _visual_children(manual.contentItem()) if x.objectName() == name)
            _click(manual, button)
            assert manual.property("chapter") == chapter
            assert manual.property("category") == "mpr-segmentation"
            assert not any(x.objectName() == "manualCategory-interaction" for x in _visual_children(manual.contentItem()))
            reading = next(x for x in _visual_children(manual.contentItem()) if x.objectName() == "voiManualReadingArea")
            assert reading.property("contentY") == 0
            assert button.mapToScene(QPointF(0, 0)).x() > category.mapToScene(QPointF(0, 0)).x()
            if chapter not in ("management", "interaction"):
                example = next(x for x in _visual_children(manual.contentItem()) if x.objectName() == "voiManualExample")
                assert example.property("sourceSize").width() > 0
            else:
                assert reading.property("contentHeight") > 0
        assert manual.grabWindow().save(str(tmp_path / (modality + "-voi-manual.png")))
        _click(manual, next(x for x in _visual_children(manual.contentItem()) if x.objectName() == "voiManualClose"))
        assert not manual.property("visible")
        assert view.isVisible() and controller.records == records_before
        # Reopen from another tool: reuse the window and jump to its chapter.
        tab.toolController.activateTool("segmentation")
        QTest.qWait(40)
        help_button = next(x for x in _visual_children(view.rootObject()) if x.objectName() == "voiManualButton")
        _click(view, help_button)
        assert view.rootObject().findChild(QObject, "operationManual") is manual
        assert manual.property("visible") and manual.property("chapter") == "segmentation"
        assert manual.size().width() == 1060 and manual.size().height() == 800
        QTest.keyClick(manual, Qt.Key_Escape)
        QTest.qWait(40)
        assert not manual.isVisible() and view.isVisible()
        _click(view, help_button)
        assert manual.isVisible()
        QTest.keySequence(manual, QKeySequence(QKeySequence.Close))
        QTest.qWait(40)
        assert not manual.isVisible() and view.isVisible()
        assert controller.records == records_before
        tab.toolController.activateTool("voi")
        QTest.qWait(40)

        # Destructive actions occupy the fixed footer, outside the scroller.
        clear_kind = next(x for x in _visual_children(view.rootObject()) if x.objectName() == "voiClearKind")
        clear_all = next(x for x in _visual_children(view.rootObject()) if x.objectName() == "voiClearAll")
        reset = next(x for x in _visual_children(view.rootObject()) if x.objectName() == "activeToolReset")
        assert clear_kind.isVisible() and clear_all.isVisible() and not reset.isVisible()
        assert clear_kind.property("text") == "清除 VOI"
        footer_y = clear_kind.mapToScene(QPointF(0, 0)).y()
        scroller = next(x for x in _visual_children(view.rootObject()) if x.objectName() == "toolDetailFlickable")
        scroller.setProperty("contentY", 40)
        assert clear_kind.mapToScene(QPointF(0, 0)).y() == footer_y
        scroller.setProperty("contentY", 0)
        assert not warnings, warnings
        assert view.grabWindow().save(str(tmp_path / (modality + "-mpr-voi.png")))
        _click(view, clear_kind)
        assert len(controller.records) == 1
        assert controller.records[0]["kind"] == "segmentation"
        assert not clear_kind.isEnabled() and clear_all.isEnabled()
        _click(view, clear_all)
        assert controller.items == []
        assert not clear_all.isEnabled()
        tab.toolController.activateTool("window")
        QTest.qWait(30)
        assert reset.isVisible() and not clear_all.isVisible()
        # Closing the application window also closes the helper window.
        tab.toolController.activateTool("segmentation")
        QTest.qWait(40)
        _click(view, next(x for x in _visual_children(view.rootObject()) if x.objectName() == "voiManualButton"))
        assert manual.isVisible()
        view.close()
        QTest.qWait(30)
        assert not manual.isVisible()
    finally:
        view.hide()
        delete(view)
        workspace.shutdown()


def _owner(item):
    parent = item
    while parent:
        if parent.property("viewportController") is not None:
            return parent.property("viewportController")
        parent = parent.parentItem()
    return None


def _click(view, item):
    QTest.mouseClick(view, Qt.LeftButton, Qt.NoModifier,
                    item.mapToScene(QPointF(item.width()/2, item.height()/2)).toPoint())
    QTest.qWait(40)
