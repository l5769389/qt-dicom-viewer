from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class WindowLevel:
    center: float
    width: float


@dataclass(frozen=True, slots=True)
class PixelSpacing:
    row: float
    column: float


@dataclass(frozen=True, slots=True)
class ImageGeometryMeta:
    rows: int
    columns: int
    pixel_spacing: PixelSpacing
    image_position_patient: tuple[float, float, float] | None
    image_orientation_patient: (
        tuple[float, float, float, float, float, float]
        | None
    )


@dataclass(frozen=True, slots=True)
class InstanceDisplayMeta:
    instance_number: int | None
    sop_instance_uid: str | None
    manufacturer: str | None
    kvp: float | None
    tube_current_ma: float | None
    slice_thickness: float | None
    rows: int | None
    columns: int | None
    pixel_spacing: tuple[float, float] | None
    image_position: tuple[float, float, float] | None
    slice_location: float | None


@dataclass(frozen=True, slots=True)
class FrameDisplayMeta:
    slice_index: int
    slice_count: int
    window: WindowLevel
    inverted: bool
    instance_meta: InstanceDisplayMeta
    geometry: ImageGeometryMeta
    # 顺序为 column、row
    crosshair_image_position: tuple[float, float] | None = None


@dataclass(frozen=True, slots=True)
class PointerDisplayMeta:
    pointer_x: float | None
    pointer_y: float | None
    pointer_ct_value: float | None


@dataclass(frozen=True, slots=True)
class DicomLoadResult:
    window: WindowLevel
    inverted: bool
    image: np.ndarray | None
    modality_pixel: np.ndarray | None
    instance_meta: InstanceDisplayMeta
