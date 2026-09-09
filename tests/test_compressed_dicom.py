"""Decode real codec streams through thumbnail, stack and volume loading paths."""

from pathlib import Path

import numpy as np
import pydicom
from pydicom.uid import (
    JPEG2000Lossless,
    JPEG2000,
    JPEGLSLossless,
    JPEGLSNearLossless,
    RLELossless,
    DeflatedExplicitVRLittleEndian,
)
import pytest

from qt_dicom_viewer.core.dicom_loader import DicomLoader
from qt_dicom_viewer.core.dicom_scanner import DicomFolderScanner
from qt_dicom_viewer.core.series_thumbnail import read_series_thumbnail
from qt_dicom_viewer.core.volume_manager import VolumeManager
from qt_dicom_viewer.core.series_export import export_series, ExportRequest
from test_dicom_tags import make_dicom, qt_app

CODECS = [
    RLELossless,
    JPEG2000Lossless,
    JPEGLSLossless,
    JPEGLSNearLossless,
    JPEG2000,
    DeflatedExplicitVRLittleEndian,
]


@pytest.mark.parametrize("syntax", CODECS, ids=lambda uid: uid.name)
def test_codec_pixels_stack_thumbnail_volume_and_anonymous_export(
    qt_app, tmp_path, syntax
):
    source = tmp_path / "input"
    source.mkdir()
    originals, expected = [], []
    for z in range(3):
        path = source / f"image-{z}.dcm"
        dataset = make_dicom(path, z + 1)
        dataset.Rows = dataset.Columns = 64
        dataset.NumberOfFrames = 1
        dataset.PixelRepresentation = 1
        dataset.BitsAllocated = dataset.BitsStored = 16
        dataset.HighBit = 15
        dataset.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        dataset.ImagePositionPatient = [0, 0, z * 2]
        dataset.PixelSpacing = [0.7, 0.8]
        dataset.RescaleSlope, dataset.RescaleIntercept = 2, -100
        stored = (
            np.add.outer(np.arange(64), np.arange(64)) * 10 - 500 + z * 20
        ).astype(np.int16)
        dataset.PixelData = stored.tobytes()
        options = dict(generate_instance_uid=False)
        tolerance = 0
        if syntax == JPEGLSNearLossless:
            options["jls_error"] = 1
            tolerance = 1
        if syntax == JPEG2000:
            options["j2k_cr"] = [2]
            tolerance = 12
        if syntax == DeflatedExplicitVRLittleEndian:
            dataset.file_meta.TransferSyntaxUID = syntax
        else:
            dataset.compress(syntax, **options)
        dataset.save_as(path, enforce_file_format=True)
        decoded = pydicom.dcmread(path)
        np.testing.assert_allclose(decoded.pixel_array, stored, atol=tolerance)
        expected.append(decoded.pixel_array.astype(np.float32) * 2 - 100)
        result = DicomLoader().load_dataset(decoded, None, False)
        np.testing.assert_array_equal(result.modality_pixel, expected[-1])
        assert not read_series_thumbnail(path).isNull()
        originals.append(path.read_bytes())
    scanned = list(DicomFolderScanner().scan(source))[-1]
    assert len(scanned.series) == 1 and scanned.dicom_file_count == 3
    volume = VolumeManager().get_or_build(scanned.series[0])
    np.testing.assert_array_equal(volume.modality_pixels, np.stack(expected))
    paths = tuple(i.path for i in scanned.series[0].instances)
    result = export_series(ExportRequest(paths, tmp_path / "output"))
    for old, new in zip(paths, sorted(result.directory.glob("*.dcm"))):
        a, b = pydicom.dcmread(old), pydicom.dcmread(new)
        assert b.PatientIdentityRemoved == "YES"
        assert a.file_meta.TransferSyntaxUID == b.file_meta.TransferSyntaxUID == syntax
        assert a.PixelData == b.PixelData
    assert [p.read_bytes() for p in paths] == originals


@pytest.mark.parametrize(
    "filename",
    [
        "JPGExtended.dcm",
        "SC_rgb_jpeg_gdcm.dcm",
        "SC_rgb_jpeg.dcm",
        "MR_small_jpeg_ls_lossless.dcm",
        "MR_small_jp2klossless.dcm",
    ],
)
def test_pydicom_bundled_reference_images_are_decoded_without_network(qt_app, filename):
    path = Path(pydicom.__file__).parent / "data/test_files" / filename
    assert path.exists(), "These decoder reference files are bundled with pydicom."
    dataset = pydicom.dcmread(path)
    values = dataset.pixel_array
    assert values.shape[:2] == (dataset.Rows, dataset.Columns)
    assert not read_series_thumbnail(path).isNull()
    if filename.startswith("MR_small"):
        original = pydicom.dcmread(path.with_name("MR_small.dcm")).pixel_array
        np.testing.assert_array_equal(values, original)
    elif filename == "JPGExtended.dcm":
        assert values.dtype == np.uint16 and values.max() > 255
    else:
        assert values.shape[2] == 3 and values.dtype == np.uint8
