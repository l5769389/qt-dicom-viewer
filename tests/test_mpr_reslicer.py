import numpy as np

from qt_dicom_viewer.application.series_catalog import SeriesCatalog
from qt_dicom_viewer.core.mpr_reslicer import MprReslicer
from qt_dicom_viewer.core.volume_manager import VolumeManager
from qt_dicom_viewer.model import (
    InstanceDisplayMeta,
    MprPlane,
    RenderRequest,
    RenderResult,
    WindowLevel,
)
from qt_dicom_viewer.model.dicom_core import (
    DicomVolume,
    MprFrame,
    MprImageGeometry,
    VolumeGeometry,
)
from qt_dicom_viewer.ui.workers.dicom_render_worker import (
    DicomRenderWorker,
)


def _instance_meta() -> InstanceDisplayMeta:
    return InstanceDisplayMeta(
        instance_number=1,
        sop_instance_uid="sop-1",
        manufacturer=None,
        kvp=None,
        tube_current_ma=None,
        slice_thickness=1.0,
        rows=3,
        columns=4,
        pixel_spacing=(1.0, 1.0),
        image_position=(0.0, 0.0, 0.0),
        slice_location=0.0,
    )


def _volume(
    pixels: np.ndarray,
    *,
    origin: tuple[float, float, float] = (0.0, 0.0, 0.0),
    row_direction: tuple[float, float, float] = (1.0, 0.0, 0.0),
    column_direction: tuple[float, float, float] = (0.0, 1.0, 0.0),
    slice_direction: tuple[float, float, float] = (0.0, 0.0, 1.0),
    slice_spacing: float = 1.0,
    row_spacing: float = 1.0,
    column_spacing: float = 1.0,
) -> DicomVolume:
    return DicomVolume(
        modality_pixels=np.ascontiguousarray(
            pixels,
            dtype=np.float32,
        ),
        geometry=VolumeGeometry(
            slice_count=pixels.shape[0],
            rows=pixels.shape[1],
            columns=pixels.shape[2],
            row_spacing=row_spacing,
            column_spacing=column_spacing,
            slice_spacing=slice_spacing,
            origin_patient=origin,
            slice_index_direction_patient=slice_direction,
            row_index_direction_patient=column_direction,
            column_index_direction_patient=row_direction,
        ),
        series_uid="series-1",
        default_window=WindowLevel(
            center=40.0,
            width=400.0,
        ),
        representative_instance_meta=_instance_meta(),
    )


def test_volume_geometry_round_trips_voxel_and_patient_coordinates() -> None:
    volume = _volume(
        np.zeros((2, 3, 4), dtype=np.float32),
        origin=(10.0, 20.0, 30.0),
        slice_spacing=2.5,
        row_spacing=0.7,
        column_spacing=0.8,
    )
    voxel = np.asarray([1.0, 2.0, 3.0, 1.0])

    patient = volume.geometry.voxel_to_patient @ voxel
    reconstructed = (
        volume.geometry.patient_to_voxel @ patient
    )

    np.testing.assert_allclose(
        patient,
        [12.4, 21.4, 32.5, 1.0],
    )
    np.testing.assert_allclose(reconstructed, voxel)


def test_mpr_frame_maps_physical_coordinates_to_patient_lps() -> None:
    frame = MprFrame.standard_lps((12.0, 22.0, 32.0))
    mpr = np.asarray([2.25, 1.0, 1.25, 1.0])

    patient = frame.mpr_to_patient @ mpr

    np.testing.assert_allclose(
        patient,
        [14.25, 23.0, 33.25, 1.0],
    )
    np.testing.assert_allclose(
        frame.patient_to_mpr @ patient,
        mpr,
    )


def test_mpr_image_geometry_uses_the_full_coordinate_chain() -> None:
    volume = _volume(
        np.zeros((4, 5, 6), dtype=np.float32),
        origin=(10.0, 20.0, 30.0),
        slice_spacing=2.5,
        row_spacing=0.7,
        column_spacing=0.8,
    )
    frame = MprFrame.standard_lps((12.0, 22.0, 32.0))
    geometry = MprImageGeometry(
        rows=5,
        columns=6,
        row_spacing=0.5,
        column_spacing=0.75,
        normal_spacing=1.25,
        frame=frame,
        top_left_mpr=(0.0, 0.0, 0.0),
        row_direction_mpr=(0.0, 1.0, 0.0),
        column_direction_mpr=(1.0, 0.0, 0.0),
        navigation_direction_mpr=(0.0, 0.0, 1.0),
        navigation_offset=0.0,
    )
    image_index = np.asarray([1.0, 2.0, 3.0, 1.0])

    mpr = geometry.image_index_to_mpr @ image_index
    patient = geometry.image_index_to_patient @ image_index
    voxel = geometry.image_index_to_voxel(
        volume.geometry
    ) @ image_index

    np.testing.assert_allclose(
        mpr,
        [2.25, 1.0, 1.25, 1.0],
    )
    np.testing.assert_allclose(
        patient,
        [14.25, 23.0, 33.25, 1.0],
    )
    np.testing.assert_allclose(
        geometry.patient_to_image_index @ patient,
        image_index,
    )
    np.testing.assert_allclose(
        voxel,
        volume.geometry.patient_to_voxel @ patient,
    )
    np.testing.assert_allclose(
        geometry.voxel_to_image_index(volume.geometry) @ voxel,
        image_index,
    )


def test_standard_planes_follow_lps_display_directions() -> None:
    pixels = np.arange(
        2 * 3 * 4,
        dtype=np.float32,
    ).reshape(2, 3, 4)
    volume = _volume(pixels)
    reslicer = MprReslicer()

    axial = reslicer.reslice(
        volume,
        MprPlane.AXIAL,
        None,
    )
    coronal = reslicer.reslice(
        volume,
        MprPlane.CORONAL,
        None,
    )
    sagittal = reslicer.reslice(
        volume,
        MprPlane.SAGITTAL,
        None,
    )

    np.testing.assert_allclose(
        axial.modality_pixels,
        pixels[1, :, :],
    )
    np.testing.assert_allclose(
        coronal.modality_pixels,
        np.stack(
            [pixels[1, 1, :], pixels[0, 1, :]],
        ),
    )
    np.testing.assert_allclose(
        sagittal.modality_pixels,
        np.stack(
            [
                pixels[1, :, 2],
                pixels[0, :, 2],
            ],
        ),
    )

    assert axial.slice_count == 2
    assert coronal.slice_count == 3
    assert sagittal.slice_count == 4

    assert axial.geometry.image_orientation_patient == (
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
    )
    assert coronal.geometry.image_orientation_patient == (
        1.0, 0.0, 0.0,
        0.0, 0.0, -1.0,
    )
    assert sagittal.geometry.image_orientation_patient == (
        0.0, 1.0, 0.0,
        0.0, 0.0, -1.0,
    )


def test_reslice_uses_the_supplied_mpr_frame_axes() -> None:
    volume = _volume(
        np.arange(
            2 * 3 * 4,
            dtype=np.float32,
        ).reshape(2, 3, 4)
    )
    frame = MprFrame(
        center_patient=volume.geometry.center_patient,
        u_direction_patient=(0.0, 1.0, 0.0),
        v_direction_patient=(-1.0, 0.0, 0.0),
        w_direction_patient=(0.0, 0.0, 1.0),
    )

    axial = MprReslicer().reslice(
        volume,
        MprPlane.AXIAL,
        None,
        frame=frame,
    )

    assert axial.geometry.frame == frame
    assert axial.geometry.image_orientation_patient == (
        0.0, 1.0, 0.0,
        -1.0, 0.0, 0.0,
    )


def test_standard_planes_preserve_directional_source_spacing() -> None:
    volume = _volume(
        np.zeros((4, 5, 6), dtype=np.float32),
        slice_spacing=0.6,
        row_spacing=0.9,
        column_spacing=1.2,
    )
    reslicer = MprReslicer()

    axial = reslicer.reslice(volume, MprPlane.AXIAL, None)
    coronal = reslicer.reslice(volume, MprPlane.CORONAL, None)
    sagittal = reslicer.reslice(volume, MprPlane.SAGITTAL, None)

    assert axial.modality_pixels.shape == (5, 6)
    assert axial.slice_count == 4
    np.testing.assert_allclose(
        [
            axial.geometry.row_spacing,
            axial.geometry.column_spacing,
            axial.geometry.normal_spacing,
        ],
        [0.9, 1.2, 0.6],
    )

    assert coronal.modality_pixels.shape == (4, 6)
    assert coronal.slice_count == 5
    np.testing.assert_allclose(
        [
            coronal.geometry.row_spacing,
            coronal.geometry.column_spacing,
            coronal.geometry.normal_spacing,
        ],
        [0.6, 1.2, 0.9],
    )

    assert sagittal.modality_pixels.shape == (4, 5)
    assert sagittal.slice_count == 6
    np.testing.assert_allclose(
        [
            sagittal.geometry.row_spacing,
            sagittal.geometry.column_spacing,
            sagittal.geometry.normal_spacing,
        ],
        [0.6, 0.9, 1.2],
    )


def test_axial_reslice_reorients_a_rotated_source_volume() -> None:
    pixels = np.arange(
        2 * 3 * 4,
        dtype=np.float32,
    ).reshape(2, 3, 4)
    volume = _volume(
        pixels,
        origin=(2.0, 0.0, 0.0),
        row_direction=(0.0, 1.0, 0.0),
        column_direction=(-1.0, 0.0, 0.0),
        slice_direction=(0.0, 0.0, 1.0),
    )

    axial = MprReslicer().reslice(
        volume,
        MprPlane.AXIAL,
        None,
    )
    expected = np.asarray(
        [
            [pixels[1, 2, 0], pixels[1, 1, 0], pixels[1, 0, 0]],
            [pixels[1, 2, 1], pixels[1, 1, 1], pixels[1, 0, 1]],
            [pixels[1, 2, 2], pixels[1, 1, 2], pixels[1, 0, 2]],
            [pixels[1, 2, 3], pixels[1, 1, 3], pixels[1, 0, 3]],
        ],
        dtype=np.float32,
    )

    np.testing.assert_allclose(
        axial.modality_pixels,
        expected,
    )


def test_trilinear_interpolation_samples_between_voxels() -> None:
    pixels = np.zeros((2, 2, 2), dtype=np.float32)
    for slice_index in range(2):
        for row_index in range(2):
            for column_index in range(2):
                pixels[slice_index, row_index, column_index] = (
                    slice_index + row_index + column_index
                )

    coordinate = np.asarray([[0.5]], dtype=np.float64)
    sampled = MprReslicer._trilinear_sample(
        pixels,
        coordinate,
        coordinate,
        coordinate,
    )

    np.testing.assert_allclose(sampled, [[1.5]])


def test_sample_count_ignores_floating_point_noise_near_integer() -> None:
    spacing = 0.24
    extent = np.nextafter(
        319 * spacing,
        np.inf,
    )

    assert MprReslicer._sample_count(extent, spacing) == 320


def test_render_worker_returns_patient_space_mpr_result(
    monkeypatch,
) -> None:
    volume = _volume(
        np.arange(
            2 * 3 * 4,
            dtype=np.float32,
        ).reshape(2, 3, 4)
    )

    catalog = SeriesCatalog()
    monkeypatch.setattr(
        catalog,
        "get_series",
        lambda series_uid: (
            object() if series_uid == "series-1" else None
        ),
    )
    volume_manager = VolumeManager()
    monkeypatch.setattr(
        volume_manager,
        "get_or_build",
        lambda series: volume,
    )
    worker = DicomRenderWorker(
        catalog,
        volume_manager,
    )
    results: list[RenderResult] = []
    worker.render_finished.connect(results.append)

    worker.handleRenderRequest(
        RenderRequest(
            request_id="request-1",
            viewport_id="viewport-coronal",
            series_uid="series-1",
            slice_index=None,
            view_type=MprPlane.CORONAL,
            window=None,
            inverted=False,
        )
    )

    assert len(results) == 1
    result = results[0]
    assert result.image is not None
    assert result.image.shape == (2, 4)
    assert result.modality_pixel is not None
    assert result.frame_meta.slice_index == 1
    assert result.frame_meta.slice_count == 3
    assert result.frame_meta.geometry.image_orientation_patient == (
        1.0, 0.0, 0.0,
        0.0, 0.0, -1.0,
    )
