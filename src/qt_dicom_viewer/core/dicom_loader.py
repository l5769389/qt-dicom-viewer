import os
from collections import OrderedDict
from datetime import date, datetime, time, timedelta
from math import exp, isfinite, log
from pathlib import Path
from typing import Any

import numpy as np
import pydicom
from pydicom import FileDataset
from pydicom.multival import MultiValue
from pydicom.pixels import apply_modality_lut
from pydicom.valuerep import DA, DT, TM

from qt_dicom_viewer.model import (
    DicomLoadResult,
    InstanceDisplayMeta,
    PixelUnitOption,
    PixelValueMeta,
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


def _string_values(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        text = str(value).strip()
        return (text,) if text else ()
    try:
        return tuple(
            text
            for item in value
            if (text := str(item).strip())
        )
    except TypeError:
        text = str(value).strip()
        return (text,) if text else ()


def _parse_dicom_datetime(value: Any) -> datetime | None:
    text = _optional_str(value)
    if text is None:
        return None
    try:
        parsed = DT(text)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, datetime) else None


def _parse_dicom_date(value: Any) -> date | None:
    text = _optional_str(value)
    if text is None:
        return None
    try:
        parsed = DA(text)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, date) else None


def _parse_dicom_time(value: Any) -> time | None:
    text = _optional_str(value)
    if text is None:
        return None
    try:
        parsed = TM(text)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, time) else None


def _combine_datetime(date_value: Any, time_value: Any) -> datetime | None:
    parsed_date = _parse_dicom_date(date_value)
    parsed_time = _parse_dicom_time(time_value)
    if parsed_date is None or parsed_time is None:
        return None
    return datetime.combine(parsed_date, parsed_time)


def _acquisition_datetime(dataset: FileDataset) -> datetime | None:
    parsed = _parse_dicom_datetime(
        getattr(dataset, "AcquisitionDateTime", None)
    )
    if parsed is not None:
        return parsed
    parsed = _combine_datetime(
        getattr(dataset, "AcquisitionDate", None),
        getattr(dataset, "AcquisitionTime", None),
    )
    if parsed is not None:
        return parsed
    return _combine_datetime(
        getattr(dataset, "SeriesDate", None),
        getattr(dataset, "SeriesTime", None),
    )


def _radiopharmaceutical_item(dataset: FileDataset):
    sequence = getattr(
        dataset,
        "RadiopharmaceuticalInformationSequence",
        None,
    )
    if sequence is None or len(sequence) != 1:
        return None
    return sequence[0]


def _radiopharmaceutical_start_datetime(
    item: Any,
    acquisition: datetime,
) -> datetime | None:
    parsed = _parse_dicom_datetime(
        getattr(item, "RadiopharmaceuticalStartDateTime", None)
    )
    if parsed is not None:
        return parsed

    parsed_time = _parse_dicom_time(
        getattr(item, "RadiopharmaceuticalStartTime", None)
    )
    if parsed_time is None:
        return None
    parsed = datetime.combine(acquisition.date(), parsed_time)
    if parsed > acquisition.replace(tzinfo=None):
        parsed -= timedelta(days=1)
    return parsed


def _comparable_datetimes(
    first: datetime,
    second: datetime,
) -> tuple[datetime, datetime]:
    first_aware = first.utcoffset() is not None
    second_aware = second.utcoffset() is not None
    if first_aware != second_aware:
        return first.replace(tzinfo=None), second.replace(tzinfo=None)
    return first, second


def _suv_unit(suv_type: str | None) -> tuple[str, str]:
    normalized = (suv_type or "BW").strip().upper()
    mapping = {
        "BW": "SUVbw",
        "BSA": "SUVbsa",
        "IBW": "SUVibw",
        "LBM": "SUVlbm",
        "LBMJAMES128": "SUVlbm",
        "LBMJANMA": "SUVlbm",
    }
    return mapping.get(normalized, f"SUV({normalized})"), normalized


def _pet_native_unit(units: str) -> str:
    return {
        "BQML": "Bq/ml",
        "CNTS": "counts",
        "CPS": "counts/s",
        "PCNT": "%",
        "NONE": "",
    }.get(units, units)


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
    def __init__(self):
        self._decoded = OrderedDict()

    def load_a_dicom(
        self,
        instance_path: Path,
        render_request: RenderRequest,
    ) -> DicomLoadResult | None:
        stat = instance_path.stat()
        key = (str(instance_path), stat.st_size, stat.st_mtime_ns)
        if key not in self._decoded:
            dataset = _read_series_dataset(instance_path)
            if dataset is None:
                return None
            self._decoded[key] = (dataset, self.to_modality_pixels(dataset))
            while len(self._decoded) > 12:
                self._decoded.popitem(last=False)
        self._decoded.move_to_end(key)
        dataset, pixels = self._decoded[key]

        return self.load_dataset(
            dataset=dataset,
            target_window=render_request.window,
            inverted=render_request.inverted,
            preferred_unit=getattr(render_request, "value_unit", None),
            modality_pixels=pixels,
        )

    def load_dataset(
        self,
        dataset: FileDataset,
        target_window: WindowLevel | None,
        inverted: bool,
        preferred_unit: str | None = None,
        modality_pixels: np.ndarray | None = None,
    ) -> DicomLoadResult:
        """Load one source DICOM frame and prepare its display result."""
        if modality_pixels is None:
            modality_pixels = self.to_modality_pixels(dataset)
        if modality_pixels.ndim != 2:
            raise ValueError(
                "Stack rendering currently requires a single-frame "
                f"2D image, got shape={modality_pixels.shape}"
            )

        display_pixels, pixel_value_meta, value_scale = (
            self.to_display_values(
                dataset,
                modality_pixels,
                preferred_unit=preferred_unit,
            )
        )
        modality = (
            _optional_str(getattr(dataset, "Modality", None)) or ""
        ).upper()
        minimum_width = (
            0.01
            if pixel_value_meta.is_suv
            else 0.001
            if modality == "PT"
            else 1.0
        )
        effective_target_window = target_window
        if (
            modality == "PT"
            and preferred_unit
            and pixel_value_meta.unit_id != preferred_unit
        ):
            # A requested quantitative unit can become unavailable on a
            # later slice. Recompute a truthful source-domain range instead
            # of applying an SUV-scale upper limit to Bq/ml values.
            effective_target_window = None
        effective_window = self.resolve_window(
            dataset=dataset,
            target_window=effective_target_window,
            modality_pixels=display_pixels,
            pixel_value_meta=pixel_value_meta,
            value_scale=value_scale,
        )
        image = self.apply_window(
            modality_pixels=display_pixels,
            target_window=effective_window,
            inverted=inverted,
            minimum_width=minimum_width,
        )

        return DicomLoadResult(
            window=effective_window,
            inverted=inverted,
            image=image,
            modality_pixel=display_pixels,
            instance_meta=self.extract_instance_meta(dataset),
            pixel_value_meta=pixel_value_meta,
        )

    def _iter_get_pixel_data(self, ordered_instance_paths: list[Path]):
        for file_path in ordered_instance_paths:
            dataset = _read_series_dataset(file_path)
            yield dataset

    @staticmethod
    def to_modality_pixels(dataset: FileDataset) -> np.ndarray:
        """Convert stored pixels with the DICOM Modality LUT/rescale."""
        stored = np.asarray(dataset.pixel_array)
        padding_mask = DicomLoader._padding_mask(stored, dataset)
        values = np.asarray(
            apply_modality_lut(stored, dataset),
            dtype=np.float32,
        )
        if padding_mask is not None:
            values = values.copy()
            values[padding_mask] = np.nan
        return np.ascontiguousarray(values, dtype=np.float32)

    @staticmethod
    def _padding_mask(
        stored_pixels: np.ndarray,
        dataset: FileDataset,
    ) -> np.ndarray | None:
        padding_value = _optional_float(
            getattr(dataset, "PixelPaddingValue", None)
        )
        if padding_value is None:
            return None
        range_limit = _optional_float(
            getattr(dataset, "PixelPaddingRangeLimit", None)
        )
        if range_limit is None:
            return stored_pixels == padding_value
        lower, upper = sorted((padding_value, range_limit))
        return (stored_pixels >= lower) & (stored_pixels <= upper)

    @staticmethod
    def to_display_values(
        dataset: FileDataset,
        modality_pixels: np.ndarray,
        *,
        preferred_unit: str | None = None,
    ) -> tuple[np.ndarray, PixelValueMeta, float]:
        modality = (_optional_str(getattr(dataset, "Modality", None)) or "").upper()
        if modality == "CT":
            return modality_pixels, PixelValueMeta(
                unit="HU",
                source_unit="HU",
                quantification="native",
            ), 1.0
        if modality != "PT":
            rescale_type = _optional_str(
                getattr(dataset, "RescaleType", None)
            )
            return modality_pixels, PixelValueMeta(
                unit=rescale_type or "",
                source_unit=rescale_type,
                quantification="native",
            ), 1.0

        units = (_optional_str(getattr(dataset, "Units", None)) or "").upper()
        suv_type = _optional_str(getattr(dataset, "SUVType", None))
        if units == "GML":
            unit, normalized_type = _suv_unit(suv_type)
            option = PixelUnitOption(
                unit_id=f"suv-{normalized_type.casefold()}",
                label=f"{'cm²/ml' if normalized_type == 'BSA' else 'g/ml'} ({unit})",
                unit=unit,
                scale_from_source=1.0,
            )
            return modality_pixels, PixelValueMeta(
                unit=unit,
                suv_type=normalized_type,
                source_unit=units,
                quantification="native",
                unit_id=option.unit_id,
                unit_options=(option,),
            ), 1.0

        if units == "BQML":
            scale, warning = DicomLoader._suvbw_scale(dataset)
            options = (
                PixelUnitOption(
                    unit_id="source",
                    label="Source (BQML)",
                    unit="Bq/ml",
                    scale_from_source=1.0,
                ),
                PixelUnitOption(
                    unit_id="kbqml",
                    label="kBq/ml",
                    unit="kBq/ml",
                    scale_from_source=0.001,
                ),
                PixelUnitOption(
                    unit_id="suvbw",
                    label="g/ml (SUVbw)",
                    unit="SUVbw",
                    scale_from_source=scale or 1.0,
                    available=scale is not None,
                    warning=warning,
                ),
            )
            available = {
                option.unit_id: option
                for option in options
                if option.available
            }
            default_unit_id = "suvbw" if scale is not None else "source"
            option = available.get(preferred_unit or "") or available[
                default_unit_id
            ]
            values = np.ascontiguousarray(
                modality_pixels * option.scale_from_source,
                dtype=np.float32,
            )
            is_suvbw = option.unit_id == "suvbw"
            return values, PixelValueMeta(
                unit=option.unit,
                suv_type="BW" if is_suvbw else None,
                source_unit=units,
                quantification=(
                    "derived"
                    if is_suvbw
                    else "unavailable"
                    if scale is None
                    else "native"
                ),
                warning=warning if scale is None else None,
                unit_id=option.unit_id,
                scale_from_source=option.scale_from_source,
                unit_options=options,
            ), option.scale_from_source

        warning = None
        quantification = "native"
        if not units:
            quantification = "unavailable"
            warning = "PET Units 缺失，当前显示值不可用于定量"
        native_unit = _pet_native_unit(units)
        option = PixelUnitOption(
            unit_id="source",
            label=f"Source ({units})" if units else "Source",
            unit=native_unit,
            scale_from_source=1.0,
        )
        return modality_pixels, PixelValueMeta(
            unit=native_unit,
            source_unit=units or None,
            quantification=quantification,
            warning=warning,
            unit_id=option.unit_id,
            unit_options=(option,),
        ), 1.0

    @staticmethod
    def _suvbw_scale(
        dataset: FileDataset,
    ) -> tuple[float | None, str | None]:
        if (
            getattr(dataset, "RescaleSlope", None) is None
            or getattr(dataset, "RescaleIntercept", None) is None
        ):
            return None, "缺少 PET Rescale Slope/Intercept，无法计算 SUVbw"

        corrected = {
            value.upper()
            for value in _string_values(
                getattr(dataset, "CorrectedImage", None)
            )
        }
        missing_corrections = sorted({"ATTN", "DECY"} - corrected)
        if missing_corrections:
            return None, (
                "缺少 PET 校正标记 " + "/".join(missing_corrections)
                + "，无法可靠计算 SUVbw"
            )

        decay_correction = (
            _optional_str(getattr(dataset, "DecayCorrection", None)) or ""
        ).upper()
        if decay_correction not in {"START", "ADMIN"}:
            return None, "Decay Correction 不是 START/ADMIN，无法计算 SUVbw"

        patient_weight_kg = _optional_float(
            getattr(dataset, "PatientWeight", None)
        )
        if patient_weight_kg is None or patient_weight_kg <= 0:
            return None, "Patient Weight 缺失或无效，无法计算 SUVbw"

        item = _radiopharmaceutical_item(dataset)
        if item is None:
            return None, "放射性药物信息缺失或不唯一，无法计算 SUVbw"
        total_dose_bq = _optional_float(
            getattr(item, "RadionuclideTotalDose", None)
        )
        half_life_seconds = _optional_float(
            getattr(item, "RadionuclideHalfLife", None)
        )
        if total_dose_bq is None or total_dose_bq <= 0:
            return None, "Radionuclide Total Dose 缺失或无效，无法计算 SUVbw"
        if half_life_seconds is None or half_life_seconds <= 0:
            return None, "Radionuclide Half Life 缺失或无效，无法计算 SUVbw"

        acquisition = _acquisition_datetime(dataset)
        if acquisition is None:
            return None, "采集日期时间缺失，无法计算 SUVbw"
        administration = _radiopharmaceutical_start_datetime(
            item,
            acquisition,
        )
        if administration is None:
            return None, "给药日期时间缺失，无法计算 SUVbw"
        acquisition, administration = _comparable_datetimes(
            acquisition,
            administration,
        )
        elapsed_seconds = (acquisition - administration).total_seconds()
        if not isfinite(elapsed_seconds) or elapsed_seconds < 0:
            return None, "给药时间晚于采集时间，无法计算 SUVbw"

        corrected_dose_bq = total_dose_bq
        if decay_correction == "START":
            corrected_dose_bq *= exp(
                -log(2.0) * elapsed_seconds / half_life_seconds
            )
        if not isfinite(corrected_dose_bq) or corrected_dose_bq <= 0:
            return None, "衰减校正后的注射剂量无效，无法计算 SUVbw"

        scale = patient_weight_kg * 1000.0 / corrected_dose_bq
        if not isfinite(scale) or scale <= 0:
            return None, "SUVbw 比例因子无效"
        return scale, None

    @staticmethod
    def resolve_window(
        dataset: FileDataset,
        target_window: WindowLevel | None,
        modality_pixels: np.ndarray | None = None,
        pixel_value_meta: PixelValueMeta | None = None,
        value_scale: float = 1.0,
    ) -> WindowLevel:
        modality = (_optional_str(getattr(dataset, "Modality", None)) or "").upper()
        minimum_width = (
            0.01
            if pixel_value_meta is not None and pixel_value_meta.is_suv
            else 0.001
            if modality == "PT"
            else 1.0
        )
        if target_window is not None:
            if modality == "PT":
                upper = max(
                    float(target_window.center)
                    + float(target_window.width) / 2.0,
                    minimum_width,
                )
                return WindowLevel(center=upper / 2.0, width=upper)
            return DicomLoader.normalize_window(
                target_window,
                minimum_width=minimum_width,
            )

        center = _optional_float(
            getattr(dataset, "WindowCenter", None)
        )
        width = _optional_float(
            getattr(dataset, "WindowWidth", None)
        )

        if center is not None and width is not None:
            if modality == "PT":
                upper = (center + width / 2.0) * value_scale
                if isfinite(upper) and upper > minimum_width:
                    return WindowLevel(
                        center=upper / 2.0,
                        width=upper,
                    )
            else:
                return DicomLoader.normalize_window(
                    WindowLevel(center=center, width=width),
                    minimum_width=minimum_width,
                )

        if modality == "PT":
            if pixel_value_meta is not None and pixel_value_meta.is_suv:
                return WindowLevel(center=2.5, width=5.0)
            finite = (
                modality_pixels[np.isfinite(modality_pixels)]
                if modality_pixels is not None
                else np.asarray([], dtype=np.float32)
            )
            if finite.size:
                high = float(np.percentile(finite, 99.5))
                if isfinite(high) and high > minimum_width:
                    return WindowLevel(
                        center=high / 2.0,
                        width=high,
                    )
                maximum = float(np.max(finite))
                if isfinite(maximum) and maximum > 0:
                    upper = max(maximum, minimum_width)
                    return WindowLevel(center=upper / 2.0, width=upper)
            # An all-padding PET frame still uses the PET intensity model.
            # Falling through to CT's 40/400 default would expose a negative
            # lower bound and misleading WL/WW semantics.
            return WindowLevel(center=0.5, width=1.0)

        return DicomLoader.normalize_window(
            WindowLevel(center=40.0, width=400.0),
            minimum_width=minimum_width,
        )

    @staticmethod
    def normalize_window(
        window: WindowLevel,
        *,
        minimum_width: float = 1.0,
    ) -> WindowLevel:
        return WindowLevel(
            center=float(window.center),
            width=max(float(window.width), minimum_width),
        )

    @staticmethod
    def apply_window(
        modality_pixels: np.ndarray,
        target_window: WindowLevel,
        inverted: bool,
        minimum_width: float = 1.0,
    ) -> np.ndarray:
        """Window any modality-valued 2D array, source stack or MPR plane."""
        effective_window = DicomLoader.normalize_window(
            target_window,
            minimum_width=minimum_width,
        )
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
        radiopharmaceutical_item = _radiopharmaceutical_item(dataset)
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
            radiopharmaceutical=(
                _optional_str(
                    getattr(
                        radiopharmaceutical_item,
                        "Radiopharmaceutical",
                        None,
                    )
                )
                if radiopharmaceutical_item is not None
                else None
            ),
            pet_units=_optional_str(getattr(dataset, "Units", None)),
            suv_type=_optional_str(getattr(dataset, "SUVType", None)),
            decay_correction=_optional_str(
                getattr(dataset, "DecayCorrection", None)
            ),
            corrected_image=_string_values(
                getattr(dataset, "CorrectedImage", None)
            ),
        )
