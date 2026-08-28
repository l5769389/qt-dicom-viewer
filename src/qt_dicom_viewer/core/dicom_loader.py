import os
from pathlib import Path
from typing import Any

import numpy as np
import pydicom
from pydicom import FileDataset
from pydicom.multival import MultiValue

from qt_dicom_viewer.model import (
    DicomLoadResult,
    InstanceDisplayMeta,
    WindowLevel, RenderRequest,
)


def _first_value(value: Any) -> Any:
    if isinstance(value, (MultiValue, list, tuple)):
        return value[0] if value else None
    return value


def _optional_float(value: Any) -> float | None:
    value = _first_value(value)
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: Any) -> int | None:
    value = _first_value(value)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_str(value: Any) -> str | None:
    value = _first_value(value)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _float_values(value: Any) -> tuple[float, ...] | None:
    if value is None or isinstance(value, (str, bytes)):
        return None
    try:
        return tuple(float(item) for item in value)
    except (TypeError, ValueError):
        return None


def _float_pair(value: Any) -> tuple[float, float] | None:
    values = _float_values(value)
    if values is None or len(values) != 2:
        return None
    return values[0], values[1]


def _float_triplet(value: Any) -> tuple[float, float, float] | None:
    values = _float_values(value)
    if values is None or len(values) != 3:
        return None
    return values[0], values[1], values[2]


def _iter_visible_files(folder: Path):
    for root, dirnames, filenames in os.walk(folder):
        # dirnames 和 os.walk(folder) 返回的对象指向同一块区域。
        # 如果采用 dirnames = xxx 。则下次遍历还会遍历.xx的文件夹。
        dirnames[:] = sorted(name for name in dirnames if not name.startswith("."))
        for filename in sorted(filenames):
            if filename.startswith("."):
                continue
            yield Path(root) / filename


def _read_series_dataset(file_path: Path) -> FileDataset | None:
    try:
        dataset = pydicom.dcmread(file_path, stop_before_pixels=False)
        return dataset
    except Exception:
        return None


class DicomLoader:
    def load_a_dicom(
        self,
        instance_path: Path,
        render_request: RenderRequest,
    ) -> DicomLoadResult | None:
        dataset = _read_series_dataset(instance_path)
        if dataset is None:
            return None

        return self.load_dataset(
            dataset=dataset,
            target_window=render_request.window,
            inverted=render_request.inverted,
        )

    def load_dataset(
        self,
        dataset: FileDataset,
        target_window: WindowLevel | None,
        inverted: bool,
    ) -> DicomLoadResult:
        """Load one source DICOM frame and prepare its display result."""
        modality_pixels = self.to_modality_pixels(dataset)
        if modality_pixels.ndim != 2:
            raise ValueError(
                "Stack rendering currently requires a single-frame "
                f"2D image, got shape={modality_pixels.shape}"
            )

        effective_window = self.resolve_window(
            dataset=dataset,
            target_window=target_window,
        )
        image = self.apply_window(
            modality_pixels=modality_pixels,
            target_window=effective_window,
            inverted=inverted,
        )

        return DicomLoadResult(
            window=effective_window,
            inverted=inverted,
            image=image,
            modality_pixel=modality_pixels,
            instance_meta=self.extract_instance_meta(dataset),
        )

    def _iter_get_pixel_data(self, ordered_instance_paths: list[Path]):
        for file_path in ordered_instance_paths:
            dataset = _read_series_dataset(file_path)
            yield dataset

    @staticmethod
    def to_modality_pixels(dataset: FileDataset) -> np.ndarray:
        """Convert stored pixel values to modality values such as CT HU."""
        slope = _optional_float(getattr(dataset, "RescaleSlope", None))
        intercept = _optional_float(getattr(dataset, "RescaleIntercept", None))
        slope = 1.0 if slope is None else slope
        intercept = 0.0 if intercept is None else intercept

        values = (
            np.asarray(dataset.pixel_array, dtype=np.float32)
            * slope
            + intercept
        )
        return np.ascontiguousarray(values, dtype=np.float32)

    @staticmethod
    def resolve_window(
        dataset: FileDataset,
        target_window: WindowLevel | None,
    ) -> WindowLevel:
        if target_window is not None:
            return DicomLoader.normalize_window(target_window)

        center = _optional_float(
            getattr(dataset, "WindowCenter", None)
        )
        width = _optional_float(
            getattr(dataset, "WindowWidth", None)
        )

        return DicomLoader.normalize_window(
            WindowLevel(
                center=40.0 if center is None else center,
                width=400.0 if width is None else width,
            )
        )

    @staticmethod
    def normalize_window(window: WindowLevel) -> WindowLevel:
        return WindowLevel(
            center=float(window.center),
            width=max(float(window.width), 1.0),
        )

    @staticmethod
    def apply_window(
        modality_pixels: np.ndarray,
        target_window: WindowLevel,
        inverted: bool,
    ) -> np.ndarray:
        """Window any modality-valued 2D array, source stack or MPR plane."""
        effective_window = DicomLoader.normalize_window(target_window)
        window_center = effective_window.center
        window_width = effective_window.width

        lower = window_center - window_width / 2
        upper = window_center + window_width / 2

        source_pixels = np.asarray(
            modality_pixels,
            dtype=np.float32,
        )
        valid_pixels = np.isfinite(source_pixels)
        displayed = np.clip(
            source_pixels,
            lower,
            upper,
        )
        displayed = (displayed - lower) / (upper - lower)
        if inverted:
            displayed = 1.0 - displayed
        displayed = np.where(
            valid_pixels,
            displayed,
            0.0,
        )

        image_8bit = (displayed * 255).astype(np.uint8)
        return np.ascontiguousarray(image_8bit)

    @staticmethod
    def extract_instance_meta(
        dataset: FileDataset,
    ) -> InstanceDisplayMeta:
        return InstanceDisplayMeta(
            instance_number=_optional_int(
                getattr(dataset, "InstanceNumber", None)
            ),
            sop_instance_uid=_optional_str(
                getattr(dataset, "SOPInstanceUID", None)
            ),
            manufacturer=_optional_str(
                getattr(dataset, "Manufacturer", None)
            ),
            kvp=_optional_float(getattr(dataset, "KVP", None)),
            tube_current_ma=_optional_float(
                getattr(dataset, "XRayTubeCurrent", None)
            ),
            slice_thickness=_optional_float(
                getattr(dataset, "SliceThickness", None)
            ),
            rows=_optional_int(getattr(dataset, "Rows", None)),
            columns=_optional_int(getattr(dataset, "Columns", None)),
            pixel_spacing=_float_pair(
                getattr(dataset, "PixelSpacing", None),
            ),
            image_position=_float_triplet(
                getattr(dataset, "ImagePositionPatient", None),
            ),
            slice_location=_optional_float(
                getattr(dataset, "SliceLocation", None)
            ),
        )
