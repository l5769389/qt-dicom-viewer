"""Decode one frame of a representative instance into a small, detached QImage."""

from pathlib import Path

import numpy as np
from pydicom import dcmread
from pydicom.dataset import Dataset
from pydicom.pixels import pixel_array, apply_modality_lut, apply_color_lut
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

from qt_dicom_viewer.core.dicom_loader import DicomLoader, _optional_float
from qt_dicom_viewer.model import WindowLevel


def read_series_thumbnail(path: Path) -> QImage:
    metadata = Dataset()
    try:
        pixels = pixel_array(path, index=0, ds_out=metadata)
    except (AttributeError, ValueError):
        # The streaming path cannot locate pixels in some deflated or legacy
        # mixed-VR files. Use the complete parser, still decoding only frame 0.
        metadata = dcmread(path)
        pixels = pixel_array(metadata, index=0)
    photometric = str(getattr(metadata, "PhotometricInterpretation", ""))
    if photometric == "PALETTE COLOR":
        pixels = apply_color_lut(pixels, metadata)
    if pixels.ndim == 2:
        pixels = np.asarray(apply_modality_lut(pixels, metadata), dtype=np.float32)
        center = _optional_float(getattr(metadata, "WindowCenter", None))
        width = _optional_float(getattr(metadata, "WindowWidth", None))
        if center is None or width is None or width <= 0:
            finite = pixels[np.isfinite(pixels)]
            low, high = np.percentile(finite, [1, 99]) if finite.size else (0.0, 1.0)
            center, width = float((low + high) / 2), max(1.0, float(high - low))
        pixels = DicomLoader.apply_window(pixels, WindowLevel(center, width), photometric == "MONOCHROME1")
        image_format = QImage.Format_Grayscale8
    elif pixels.ndim == 3 and pixels.shape[2] in (3, 4):
        if pixels.dtype != np.uint8:
            maximum = float(np.iinfo(pixels.dtype).max) if photometric == "PALETTE COLOR" else (
                2 ** int(getattr(metadata, "BitsStored", 8)) - 1)
            pixels = np.clip(pixels.astype(np.float32) * 255 / max(1, maximum), 0, 255).astype(np.uint8)
        image_format = QImage.Format_RGB888 if pixels.shape[2] == 3 else QImage.Format_RGBA8888
    else:
        raise ValueError("Unsupported thumbnail pixel shape")
    pixels = np.ascontiguousarray(pixels)
    height, width = pixels.shape[:2]
    image = QImage(pixels.data, width, height, pixels.strides[0], image_format).copy()
    return image.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
