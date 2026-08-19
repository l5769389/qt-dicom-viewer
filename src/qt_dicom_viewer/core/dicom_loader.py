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


def _read_series_dataset(file_path) -> FileDataset | None:
    try:
        dataset = pydicom.dcmread(file_path, stop_before_pixels=False)
        return dataset
    except Exception:
        return None

class DicomLoader():
    def load_a_dicom(self, instance_path: Path,
                            render_request: RenderRequest,

                     ) -> DicomLoadResult | None:
        dataset = _read_series_dataset(instance_path)
        if dataset is not None:
            request_window: WindowLevel | None = render_request.window
            inverted = render_request.inverted
            return self.apply_window(dataset,request_window, inverted)
        return None

    def _iter_get_pixel_data(self,ordered_instance_paths: list[Path]):
        for file_path in ordered_instance_paths:
            dataset = _read_series_dataset(file_path)
            yield dataset


    def apply_window(self,dataset: FileDataset,
                        target_window: WindowLevel | None,
                     inverted: bool
                     ) -> DicomLoadResult:
        slope = float(getattr(dataset, "RescaleSlope", 1))
        intercept = float(getattr(dataset, "RescaleIntercept", 0))
        values = dataset.pixel_array.astype(np.float32) * slope + intercept
        if target_window is not None:
            window_center = target_window.center
            window_width = target_window.width
        else:
            window_center = _optional_float(getattr(dataset, "WindowCenter", None))
            window_width = _optional_float(getattr(dataset, "WindowWidth", None))
            window_center = 40.0 if window_center is None else window_center
            window_width = 400.0 if window_width is None else window_width

        if window_width <= 0:
            window_width = 1.0

        lower = window_center - window_width / 2
        upper = window_center + window_width / 2

        displayed = np.clip(values, lower, upper)
        displayed = (displayed - lower) / (upper - lower)
        if inverted:
            displayed = 1.0 - displayed
        # 5. 转成 QImage 可显示的 8-bit 灰度
        image_8bit = (displayed * 255).astype(np.uint8)
        image_8bit = np.ascontiguousarray(image_8bit)
        modality_pixels = (
                dataset.pixel_array.astype(np.float32)
                * slope
                + intercept
        )
        return DicomLoadResult(
            window=WindowLevel(
                window_center,
                window_width,
            ),
            inverted=inverted,
            image= image_8bit,
            modality_pixel = modality_pixels,
            instance_meta=InstanceDisplayMeta(
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
            ),
        )
