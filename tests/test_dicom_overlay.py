import numpy as np
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from qt_dicom_viewer.core.dicom_loader import DicomLoader
from qt_dicom_viewer.model import (
    DicomFolderScanSnapshot,
    DicomInstanceMeta,
    DicomLoadResult,
    DicomSeriesRecord,
    FrameDisplayMeta,
    ImageGeometryMeta,
    InstanceDisplayMeta,
    PixelSpacing,
    RenderRequest,
    RenderResult,
    SeriesDisplayMeta,
    TwoDViewType,
    ViewportConfig,
    WindowLevel,
)
from qt_dicom_viewer.ui.controller.viewport.viewport_controller import (
    ViewportController,
)
from qt_dicom_viewer.application.series_catalog import SeriesCatalog
from qt_dicom_viewer.ui.workers.dicom_render_worker import (
    DicomRenderWorker,
)
from qt_dicom_viewer.ui.controller.tab.tool_controller import ToolController


def _ct_dataset() -> FileDataset:
    file_meta = FileMetaDataset()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    dataset = FileDataset(
        None,
        {},
        file_meta=file_meta,
        preamble=b"\0" * 128,
    )
    dataset.Rows = 2
    dataset.Columns = 2
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 16
    dataset.BitsStored = 16
    dataset.HighBit = 15
    dataset.PixelRepresentation = 1
    dataset.PixelData = np.array(
        [[-1000, 0], [40, 1000]],
        dtype=np.int16,
    ).tobytes()

    dataset.RescaleSlope = 1
    dataset.RescaleIntercept = 0
    dataset.WindowCenter = [40, 80]
    dataset.WindowWidth = [400, 1500]
    dataset.InstanceNumber = 7
    dataset.SOPInstanceUID = generate_uid()
    dataset.Manufacturer = "Example Medical"
    dataset.KVP = 120
    dataset.XRayTubeCurrent = 250
    dataset.SliceThickness = 1.25
    dataset.PixelSpacing = [0.7, 0.8]
    dataset.ImagePositionPatient = [-120.5, -90.25, 42]
    dataset.SliceLocation = 42
    return dataset


def test_dicom_loader_extracts_overlay_metadata() -> None:
    result = DicomLoader().apply_window(_ct_dataset(), None, False)

    assert result.image is not None
    assert result.image.shape == (2, 2)
    assert result.image.dtype == np.uint8
    assert result.window == WindowLevel(center=40.0, width=400.0)

    meta = result.instance_meta
    assert meta.instance_number == 7
    assert meta.manufacturer == "Example Medical"
    assert meta.kvp == 120.0
    assert meta.tube_current_ma == 250.0
    assert meta.slice_thickness == 1.25
    assert meta.pixel_spacing == (0.7, 0.8)
    assert meta.image_position == (-120.5, -90.25, 42.0)
    assert meta.slice_location == 42.0


def test_dicom_loader_allows_missing_optional_overlay_tags() -> None:
    dataset = _ct_dataset()
    for keyword in (
        "Manufacturer",
        "KVP",
        "XRayTubeCurrent",
        "SliceThickness",
        "PixelSpacing",
        "ImagePositionPatient",
        "SliceLocation",
    ):
        delattr(dataset, keyword)

    result = DicomLoader().apply_window(dataset, None, False)

    assert result.image is not None
    assert result.instance_meta.manufacturer is None
    assert result.instance_meta.kvp is None
    assert result.instance_meta.tube_current_ma is None
    assert result.instance_meta.slice_thickness is None
    assert result.instance_meta.pixel_spacing is None
    assert result.instance_meta.image_position is None
    assert result.instance_meta.slice_location is None


def test_viewport_overlay_formats_series_and_frame_values() -> None:
    series_meta = SeriesDisplayMeta(
        patient_name="Example Patient",
        patient_id="P001",
        study_description="Chest",
        series_description="Axial CT",
        modality="CT",
        series_uid="series-1",
    )
    controller = ViewportController(
        viewport_config=ViewportConfig(
            viewport_id="viewport-1",
            tab_id="tab-1",
            viewport_type=TwoDViewType.STACK,
            series_uid="series-1",
            series_meta=series_meta,
        ),
        tool_controller=ToolController(),
    )
    instance_meta = InstanceDisplayMeta(
        instance_number=7,
        sop_instance_uid="sop-1",
        manufacturer="Example Medical",
        kvp=120.0,
        tube_current_ma=250.0,
        slice_thickness=1.25,
        rows=512,
        columns=512,
        pixel_spacing=(0.7, 0.8),
        image_position=(-120.5, -90.25, 42.0),
        slice_location=42.0,
    )
    controller.handleRenderResult(
        RenderResult(
            response_id="request-1",
            viewport_id="viewport-1",
            series_uid="series-1",
            view_type=TwoDViewType.STACK,
            image=np.zeros((2, 2), dtype=np.uint8),
            modality_pixel=np.zeros((2, 2), dtype=np.float32),
            frame_meta=FrameDisplayMeta(
                slice_index=6,
                slice_count=100,
                window=WindowLevel(center=40.0, width=400.0),
                inverted=False,
                instance_meta=instance_meta,
                geometry=ImageGeometryMeta(
                    rows=512,
                    columns=512,
                    pixel_spacing=PixelSpacing(row=0.7, column=0.8),
                    image_position_patient=(-120.5, -90.25, 42.0),
                    image_orientation_patient=None,
                ),
            ),
        )
    )

    overlay = controller.overlayInfo
    assert overlay["patientName"] == "Example Patient"
    assert overlay["sliceIndex"] == "7"
    assert overlay["sliceCount"] == "100"
    assert overlay["pixelSpacingX"] == "0.8"
    assert overlay["pixelSpacingY"] == "0.7"
    assert overlay["positionZ"] == "42"
    assert overlay["windowCenter"] == "40"
    assert overlay["windowWidth"] == "400"


def test_render_worker_builds_frame_meta(monkeypatch, tmp_path) -> None:
    instance_meta = InstanceDisplayMeta(
        instance_number=1,
        sop_instance_uid="sop-1",
        manufacturer=None,
        kvp=None,
        tube_current_ma=None,
        slice_thickness=None,
        rows=2,
        columns=2,
        pixel_spacing=None,
        image_position=None,
        slice_location=None,
    )
    load_result = DicomLoadResult(
        window=WindowLevel(center=40, width=400),
        inverted=False,
        image=np.zeros((2, 2), dtype=np.uint8),
        modality_pixel=np.zeros((2, 2), dtype=np.float32),
        instance_meta=instance_meta,
    )
    monkeypatch.setattr(
        DicomLoader,
        "load_a_dicom",
        lambda self, instance_path, render_request: load_result,
    )

    instance_path = tmp_path / "slice.dcm"
    catalog = SeriesCatalog()
    catalog.update(
        DicomFolderScanSnapshot(
            folder=tmp_path,
            total_file_count=1,
            dicom_file_count=1,
            skipped_file_count=0,
            series=[
                DicomSeriesRecord(
                    patient_name="Example Patient",
                    patient_id="P001",
                    study_description="Chest",
                    study_instance_uid="study-1",
                    series_description="Axial CT",
                    series_instance_uid="series-1",
                    series_number=1,
                    modality="CT",
                    instances=(
                        DicomInstanceMeta(
                            path=instance_path,
                            patient_name="Example Patient",
                            patient_id="P001",
                            study_description="Chest",
                            study_instance_uid="study-1",
                            series_description="Axial CT",
                            series_instance_uid="series-1",
                            series_number=1,
                            instance_number=1,
                            sop_instance_uid="sop-1",
                            pixel_spacing=PixelSpacing(row=0.7, column=0.8),
                            modality="CT",
                            rows=2,
                            columns=2,
                            transfer_syntax="Explicit VR Little Endian",
                            image_position_patient=(0.0, 0.0, 0.0),
                            image_orientation_patient=(
                                1.0, 0.0, 0.0,
                                0.0, 1.0, 0.0,
                            ),
                            slice_thickness=1.0,
                        ),
                    ),
                )
            ],
        )
    )

    worker = DicomRenderWorker(catalog)
    results: list[RenderResult] = []
    worker.render_finished.connect(results.append)
    worker.handleRenderRequest(
        RenderRequest(
            request_id="request-1",
            viewport_id="viewport-1",
            series_uid="series-1",
            view_type=TwoDViewType.STACK,
            slice_index=0,
            window=None,
            inverted=False,
        )
    )

    assert len(results) == 1
    assert results[0].frame_meta.slice_index == 0
    assert results[0].frame_meta.slice_count == 1
    assert results[0].frame_meta.instance_meta is instance_meta
    assert results[0].frame_meta.geometry.pixel_spacing == PixelSpacing(
        row=0.7,
        column=0.8,
    )
