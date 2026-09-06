from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QUrl, Qt, QPointF, QMetaObject
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest
from shiboken6 import delete

from test_pet_fusion import paired_series
from test_measurement_qml import qt_app, _visual_children, _scene, _mouse_drag
from qt_dicom_viewer.ui.controller.panel_controller import PanelController
from qt_dicom_viewer.ui.controller.workspace_controller import WorkspaceController
from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
from qt_dicom_viewer.core.pet_reconstruction import PetReconstructor
from qt_dicom_viewer.core.volume_manager import VolumeManager


@pytest.mark.parametrize("fusion", [False, True])
def test_real_pet_workspace(qt_app, paired_series, tmp_path, fusion):
    catalog, ct, pet = paired_series
    provider = DicomImageProvider()
    workspace = WorkspaceController(catalog, provider)
    panel = PanelController(series_catalog=catalog)
    panel._scan_series_record = {r.series_instance_uid: r for r in (ct, pet)}
    renderer = PetReconstructor(catalog, VolumeManager())
    workspace.renderRequested.connect(lambda request: workspace.handleRenderResult(renderer.render(request)))
    if fusion:
        workspace.createFusionTab(ct.series_instance_uid, pet.series_instance_uid)
    else:
        workspace.createTab(pet.series_instance_uid, "PET MPR", "mpr")
    tab = next(iter(workspace._tab_dict.values()))
    tab.toolController.selectInteraction("window")
    view = QQuickView()
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.resize(1540, 1000)
    view.engine().addImageProvider("dicom", provider)
    warnings = []
    view.engine().warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    view.setInitialProperties({"workspace": workspace, "panel": panel})
    view.setSource(QUrl.fromLocalFile(str(Path(__file__).parent / "qml/PetWorkspace.qml")))
    assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
    view.show()
    QTest.qWait(80)
    try:
        items = list(_visual_children(view.rootObject()))
        layers = [x for x in items if x.objectName() == "dicomPixelLayer"]
        assert len(layers) == 4
        assert any(x.objectName() == "petWorkspacePanel" and x.isVisible() for x in items)
        palette = next(x for x in items if x.objectName() == "petColorMap")
        tab.toolController.settingsController.setValue("colormap", "pet", "cardiac")
        QTest.qWait(30)
        assert palette.property("currentText") == "Cardiac"
        assert all(v.activeColorMap == "cardiac" for v in tab.viewports_by_id.values()
                   if v.viewportRole not in ("ct", "fusion"))
        if fusion:
            fusion_palette = next(x for x in items if x.objectName() == "fusionColorMap")
            tab.setFusionColorMap("hotMetal")
            QTest.qWait(30)
            assert fusion_palette.property("currentText") == "Hot Metal"
        kbq = next(x for x in items if x.objectName() == "petUnit-kbqml")
        QTest.mouseClick(view, Qt.LeftButton, Qt.NoModifier,
                        kbq.mapToScene(QPointF(kbq.width()/2, kbq.height()/2)).toPoint())
        QTest.qWait(40)
        assert tab.petController.petActiveUnitId == "kbqml"
        assert tab.petController.petControlUpper == 15
        mip = next(v for v in tab.viewports_by_id.values() if v.viewportRole == "mip")
        result = mip._mip_result
        row, col = np.unravel_index(np.nanargmax(result.modality_pixel), result.modality_pixel.shape)
        peak = result.peak_positions[row, col].copy()
        QTest.mouseClick(view, Qt.LeftButton, Qt.NoModifier, _scene(layers[3], col, row))
        QTest.qWait(20)
        np.testing.assert_allclose(tab._target_mpr_state.frame.center_patient, peak)
        if fusion:
            tab.setRegistrationActive(True)
            before = tab.matrix.copy()
            _mouse_drag(view, _scene(layers[2], 1., 1.), _scene(layers[2], 2., 1.))
            assert not np.allclose(tab.matrix, before)
            before = tab.matrix.copy()
            QTest.mousePress(view, Qt.RightButton, Qt.NoModifier, _scene(layers[2], .5, .5))
            QTest.mouseMove(view, _scene(layers[2], 1., 1.), 20)
            QTest.mouseMove(view, _scene(layers[2], .5, 1.5), 20)
            QTest.mouseRelease(view, Qt.RightButton, Qt.NoModifier, _scene(layers[2], .5, 1.5))
            QTest.qWait(20)
            assert not np.allclose(tab.matrix[:3, :3], before[:3, :3])
            QTest.keyClick(view, Qt.Key_Escape)
            assert not tab.registrationActive
            tab.setPlane("coronal")
            QTest.qWait(40)
        # Enter a large custom control value; formatting must keep trailing zeros.
        items = list(_visual_children(view.rootObject()))
        control = next(x for x in items if x.objectName() == "petControlUpperInput")
        control.forceActiveFocus()
        QMetaObject.invokeMethod(control, "selectAll")
        for char in "10000":
            QTest.keyClick(view, char)
        QTest.keyClick(view, Qt.Key_Return)
        QTest.qWait(20)
        assert tab.petController.petControlUpper == 10000
        assert control.property("text") == "10000"
        assert not warnings, warnings
        preview = tmp_path / ("petct-fusion.png" if fusion else "pet-mpr.png")
        assert view.grabWindow().save(str(preview))
        print(f"PET workspace preview: {preview}")
    finally:
        view.hide()
        delete(view)
        workspace.shutdown()
        panel.shutdown()


def test_main_qml_two_selection_entry_points(qt_app, paired_series, tmp_path):
    from PySide6.QtQml import QQmlApplicationEngine
    from test_tag_qml import _App, find, click
    catalog, ct, pet = paired_series
    provider = DicomImageProvider()
    workspace = WorkspaceController(catalog, provider)
    panel = PanelController(series_catalog=catalog)
    panel._scan_series_record = {r.series_instance_uid: r for r in (ct, pet)}
    panel.fusionCreateRequested.connect(workspace.createFusionTab)
    renderer = PetReconstructor(catalog, VolumeManager())
    workspace.renderRequested.connect(lambda r: workspace.handleRenderResult(renderer.render(r)))
    app = _App(workspace, panel)
    engine = QQmlApplicationEngine()
    engine.addImageProvider("dicom", provider)
    engine.rootContext().setContextProperty("appController", app)
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    engine.load(QUrl.fromLocalFile(str(Path(__file__).resolve().parents[1] / "src/qt_dicom_viewer/qml/Main.qml")))
    window = engine.rootObjects()[0]
    QTest.qWait(40)
    try:
        click(window, find(window, "series-" + pet.series_instance_uid))
        item = find(window, "series-" + ct.series_instance_uid)
        pos = item.mapToScene(QPointF(item.width()/2, item.height()/2)).toPoint()
        QTest.mouseClick(window, Qt.LeftButton, Qt.ControlModifier, pos)
        QTest.qWait(20)
        assert len(panel.selectedSeriesUids) == 2
        click(window, find(window, "openView-fusion"))
        assert workspace.activeTabType == "petctfusion"
        assert len(workspace.currentTabAllViewports) == 4
        click(window, find(window, "series-" + ct.series_instance_uid))
        click(window, find(window, "openView-fusion"))
        assert panel.fusionDialogOpen
        candidates = find(window, "fusionCandidates")
        assert candidates.property("count") == 1
        # Candidate is the first visual delegate within ListView's content item.
        candidate = find(window, "fusionCandidate-" + pet.series_instance_uid)
        click(window, candidate)
        click(window, find(window, "confirmFusion"))
        assert not panel.fusionDialogOpen
        assert len(workspace.tabs) == 1
        assert not warnings, warnings
        assert window.grabWindow().save(str(tmp_path / "petct-main.png"))
    finally:
        window.hide()
        delete(engine)
        workspace.shutdown()
        panel.shutdown()
