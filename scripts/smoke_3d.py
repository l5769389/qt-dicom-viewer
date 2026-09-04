"""Real-window 3D smoke test. Run separately from headless pytest.

    uv run python scripts/smoke_3d.py

Creates temporary synthetic DICOM files and exercises the actual QML/worker/VTK
path. Requires a desktop session and OpenGL. No patient data is used.
"""
from dataclasses import replace
from importlib.resources import files
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import time
import traceback

import numpy as np
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian, generate_uid
from PySide6.QtCore import QPoint, QPointF, QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from qt_dicom_viewer.app import bind_controller
from qt_dicom_viewer.core.dicom_scanner import _read_instance, _build_series_record
from qt_dicom_viewer.core.volume_view import VolumeViewState
from qt_dicom_viewer.model.volume_models import VolumeDisplayState
from qt_dicom_viewer.model import DicomFolderScanSnapshot, TabType


def make_series(folder):
    series_uid, study_uid = generate_uid(), generate_uid()
    z, y, x = np.mgrid[-1:1:48j, -1:1:64j, -1:1:64j]
    pixels = np.full(x.shape, -1000, dtype=np.int16)
    pixels[(x/0.65)**2+(y/0.8)**2+(z/0.85)**2 < 1] = 100
    pixels[((x+0.25)/0.18)**2+(y/0.42)**2+(z/0.6)**2 < 1] = -650
    pixels[((x-0.2)/0.15)**2+((y+0.2)/0.2)**2+(z/0.65)**2 < 1] = 400
    pixels[((x-0.23)/0.2)**2+(y/0.23)**2+(z/0.65)**2 < 1] = 800
    instances = []
    for index, plane in enumerate(pixels):
        path = folder / f"{index:03}.dcm"
        meta = FileMetaDataset()
        meta.TransferSyntaxUID = ExplicitVRLittleEndian
        meta.MediaStorageSOPClassUID = CTImageStorage
        meta.MediaStorageSOPInstanceUID = generate_uid()
        ds = FileDataset(str(path), {}, file_meta=meta, preamble=b"\0"*128)
        ds.SOPClassUID, ds.SOPInstanceUID = CTImageStorage, meta.MediaStorageSOPInstanceUID
        ds.StudyInstanceUID, ds.SeriesInstanceUID = study_uid, series_uid
        ds.PatientName, ds.PatientID = "Synthetic^Phantom", "SMOKE-3D"
        ds.SeriesDescription, ds.Modality = "Synthetic 3D phantom", "CT"
        ds.InstanceNumber = index+1
        ds.Rows, ds.Columns = plane.shape
        ds.PixelSpacing, ds.SliceThickness = [1, 1], 1.5
        ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        ds.ImagePositionPatient = [-32, -32, -36+1.5*index]
        ds.BitsAllocated, ds.BitsStored, ds.HighBit = 16, 16, 15
        ds.SamplesPerPixel, ds.PixelRepresentation = 1, 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.RescaleIntercept, ds.RescaleSlope = 0, 1
        ds.WindowCenter, ds.WindowWidth = 400, 1000
        ds.PixelData = plane.tobytes()
        ds.save_as(path, enforce_file_format=True)
        instances.append(_read_instance(path))
    return _build_series_record(instances)


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    temp = TemporaryDirectory(prefix="qt-dicom-3d-")
    series = make_series(Path(temp.name))
    second = replace(series, series_instance_uid=generate_uid(), series_description="Second phantom")
    engine = bind_controller()
    controller = engine.app_controller
    controller._series_catalog.update(DicomFolderScanSnapshot(
        Path(temp.name), 48, 48, 0, [series, second]))
    warnings = []
    engine.warnings.connect(lambda messages: warnings.extend(m.toString() for m in messages))
    engine.load(files("qt_dicom_viewer").joinpath("qml/Main.qml"))
    assert engine.rootObjects(), "QML root failed to load"
    root = engine.rootObjects()[0]
    workspace = controller.workspaceController
    workspace.createTab(series.series_instance_uid, "Synthetic phantom", TabType.THREE_D)
    first = workspace.activeViewport
    first_id = workspace.activeTabId
    errors = []

    def pump(milliseconds=300):
        # Let the Python render worker run too; QTest.qWait can retain the GIL.
        deadline = time.monotonic()+milliseconds/1000
        while time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.005)

    def ready(viewport):
        deadline = time.monotonic()+10
        while viewport.loadState in ("idle", "loading") and time.monotonic() < deadline:
            pump(50)
        assert viewport.loadState == "ready", (viewport.loadState, viewport.errorMessage)
        pump(500)
        assert viewport.loadState == "ready", viewport.errorMessage
        assert viewport._host.backend._initialized
        assert viewport.nativeWindow.parent() == root
        assert viewport._host.isVisible()

    def capture(viewport, filename):
        from vtkmodules.vtkRenderingCore import vtkWindowToImageFilter
        from vtkmodules.vtkIOImage import vtkPNGWriter
        from vtkmodules.util.numpy_support import vtk_to_numpy
        grab = vtkWindowToImageFilter()
        grab.SetInput(viewport._host.backend.window)
        grab.ReadFrontBufferOff()
        grab.Update()
        array = vtk_to_numpy(grab.GetOutput().GetPointData().GetScalars())
        assert np.count_nonzero(array.max(axis=1) > 80) > 1000, "Empty framebuffer"
        if filename:
            writer = vtkPNGWriter()
            writer.SetFileName(str(filename))
            writer.SetInputConnection(grab.GetOutputPort())
            writer.Write()
        return array.copy()

    def visual_children(item):
        yield item
        for child in item.childItems():
            yield from visual_children(child)

    def find_item(name):
        return next(item for item in visual_children(root.contentItem())
                    if item.objectName() == name and item.isVisible())

    def click_item(name):
        button = find_item(name)
        assert button.isEnabled(), name
        if name.startswith("volumePreset-"):
            flickable = find_item("toolDetailFlickable")
            local = button.mapToItem(flickable, QPointF(button.width()/2, button.height()/2))
            if local.y() < 0 or local.y() > flickable.height():
                target = flickable.property("contentY") + local.y() - flickable.height()/2
                maximum = max(0, flickable.property("contentHeight")-flickable.height())
                flickable.setProperty("contentY", min(max(0, target), maximum))
                pump(20)
        point = button.mapToScene(QPointF(button.width()/2, button.height()/2)).toPoint()
        QTest.mouseClick(root, Qt.LeftButton, pos=point)
        pump(50)

    def select_tool(name):
        click_item("primaryTool-"+name)

    def sample_anatomy(array, widget):
        w, h = widget.GetRenderWindow().GetSize()
        return array.reshape(h, w, 3)[h//5:4*h//5, w//5:4*w//5]

    def exercise():
        try:
            ready(first)
            print("3D loaded and embedded", first._host.size(), flush=True)
            backend = first._host.backend
            started = time.perf_counter()
            backend.render(first.state, True, first.display_state)
            interactive_elapsed = time.perf_counter()-started
            interactive_frame = capture(first, None)
            started = time.perf_counter()
            backend.render(first.state, False, first.display_state)
            settled_elapsed = time.perf_counter()-started
            settled_frame = capture(first, None)
            quality_delta = np.abs(interactive_frame.astype(np.int16)-settled_frame.astype(np.int16))
            assert quality_delta.max() <= 1
            assert np.mean(quality_delta) < 0.01
            print(f"PASS: fixed interaction quality (pixel delta {np.mean(quality_delta):.4f}, "
                  f"interactive {interactive_elapsed*1000:.1f} ms, settled {settled_elapsed*1000:.1f} ms)",
                  flush=True)
            before = capture(first, None)
            marker_initial = first._host.backend.marker.GetRenderer().GetActiveCamera().GetDirectionOfProjection()
            widget = first._host.vtk_widget
            center = QPoint(widget.width()//2, widget.height()//2)
            QTest.mousePress(widget, Qt.LeftButton, pos=center)
            QTest.mouseMove(widget, center+QPoint(95, 50))
            QTest.mouseRelease(widget, Qt.LeftButton, pos=center+QPoint(95, 50))
            pump()
            assert first.state.rotation != VolumeViewState().rotation
            after = capture(first, sys.argv[1] if len(sys.argv) > 1 else None)
            assert np.mean(np.abs(after.astype(float)-before.astype(float))) > 0.1
            marker_rotated = first._host.backend.marker.GetRenderer().GetActiveCamera().GetDirectionOfProjection()
            assert not np.allclose(marker_initial, marker_rotated)
            np.testing.assert_allclose(marker_rotated,
                first._host.backend.renderer.GetActiveCamera().GetDirectionOfProjection())
            select_tool("volume-direction")
            for face in ("P", "L", "R", "S", "I", "A"):
                click_item("volumeFace-"+face)
                assert first.currentFace == face
                assert find_item("currentVolumeFace").property("text") == face
                assert find_item("volumeFace-"+face).property("checked")
            QTest.mousePress(widget, Qt.LeftButton, pos=center)
            QTest.mouseRelease(widget, Qt.LeftButton, pos=center+QPoint(300, 40))
            pump()
            assert find_item("currentVolumeFace").property("text") == first.currentFace
            assert first.currentFace != "A"
            assert sum(find_item("volumeFace-"+f).property("checked") for f in "AP LRSI".replace(" ", "")) == 1
            click_item("volumeFace-A")
            select_tool("volume-preset")
            frames = {}
            image_data = first._host.backend.mapper.GetInput()
            for preset_id in ("general", "bone", "lung", "vessel", "mip", "xray"):
                click_item("volumePreset-"+preset_id)
                pump()
                assert first.currentPresetId == preset_id, (preset_id, first.currentPresetId)
                assert find_item("volumePreset-"+preset_id).property("checked")
                filename = (Path(sys.argv[1]).with_stem(Path(sys.argv[1]).stem+"-"+preset_id)
                            if len(sys.argv) > 1 else None)
                frames[preset_id] = sample_anatomy(capture(first, filename), widget)
                assert np.count_nonzero(frames[preset_id].max(axis=2) > 20) > 500, preset_id
                assert first._host.backend.mapper.GetInput() is image_data
            for name in ("bone", "lung", "vessel", "mip", "xray"):
                assert np.mean(np.abs(frames[name].astype(float)-frames["general"].astype(float))) > 0.1, name
            assert np.mean(frames["xray"] > 250) < 0.1, "XRay saturated"
            click_item("volumePreset-bone")
            select_tool("window")
            assert workspace.activeTab.toolController.activePanel == ""
            original_display = first.display_state
            pose = first.state
            QTest.mousePress(widget, Qt.LeftButton, pos=center)
            QTest.mouseRelease(widget, Qt.LeftButton, pos=center+QPoint(100, -100))
            pump()
            assert first.windowCenter > original_display.window.center
            assert first.windowWidth > original_display.window.width
            assert first.state == pose
            changed = sample_anatomy(capture(first, None), widget)
            assert np.mean(np.abs(changed.astype(float)-frames["bone"].astype(float))) > 0.1
            click_item("activeToolReset")
            assert first.display_state == original_display
            print("PASS: six faces, QML direction tracking, all six presets, drag window/reset", flush=True)
            select_tool("pan")
            QTest.mousePress(widget, Qt.LeftButton, pos=center)
            QTest.mouseRelease(widget, Qt.LeftButton, pos=center+QPoint(30, 15))
            assert first.state.pan != (0, 0)
            select_tool("zoom")
            QTest.mousePress(widget, Qt.LeftButton, pos=center)
            QTest.mouseRelease(widget, Qt.LeftButton, pos=center+QPoint(0, -80))
            assert first.state.zoom > 1
            saved = first.state
            saved_display = first.display_state
            marker_before = first._host.backend.marker.GetRenderer().GetActiveCamera().GetDirectionOfProjection()
            pump()
            marker_after = first._host.backend.marker.GetRenderer().GetActiveCamera().GetDirectionOfProjection()
            np.testing.assert_allclose(marker_before, marker_after)
            root.resize(1200, 700)
            pump()
            assert widget.width() < 800 and widget.height() > 400
            workspace.createTab(series.series_instance_uid, "2D phantom", TabType.TWO_D)
            pump()
            assert not first._host.isVisible()
            assert first.nativeWindow.parent() is None
            workspace.activateTabId(first_id)
            pump()
            ready(first)
            assert first.state == saved
            assert first.display_state == saved_display
            workspace.createTab(second.series_instance_uid, "Second phantom", TabType.THREE_D)
            other = workspace.activeViewport
            ready(other)
            assert other.state == VolumeViewState()
            assert other.currentPresetId == "general"
            assert not first._host.isVisible()
            workspace.closeTab(workspace.activeTabId)
            pump()
            assert other.nativeWindow is None
            workspace.activateTabId(first_id)
            pump()
            ready(first)
            select_tool("reset")
            assert first.state == VolumeViewState()
            assert first.display_state == VolumeDisplayState(window=first.volume.default_window)
            workspace.closeTab(first_id)
            pump()
            assert first.nativeWindow is None
            workspace.createTab(series.series_instance_uid, "Reopened phantom", TabType.THREE_D)
            ready(workspace.activeViewport)
            assert not warnings, "\n".join(warnings)
            print("PASS: render, drag tools, cube, resize, 2D/3D switching, independent tabs, close/reopen", flush=True)
        except BaseException:
            errors.append(traceback.format_exc())
            print(errors[-1], flush=True)
        finally:
            controller.shutdown()
            root.close()
            app.quit()

    QTimer.singleShot(100, exercise)
    app.exec()
    temp.cleanup()
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
