from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
from enum import StrEnum

import numpy as np

class TabType(StrEnum):
    TWO_D = "2d"
    MPR = "mpr"
    THREE_D = "3d"
    FOUR_D = "4d"
    TAG = "tag"


class ViewType(StrEnum):
    TWO_D = "2d"
    MPR = "mpr"
    THREE_D = "3d"
    FOUR_D = "4d"


# 一级按钮
class ToolType(StrEnum):
    WINDOW = 'window'
    PAN = 'pan'
    ZOOM = 'zoom'
    SCROLL = 'scroll'
    MEASURE = 'measure'
    ANNOTATE = 'annotate'
    ROTATE = 'rotate'
    RESET = 'reset'



@dataclass(frozen=True, slots=True)
class WindowLevel:
    center: float
    width: float


@dataclass(frozen=True, slots=True)
class RenderRequest:
    request_id: str
    viewport_id: str
    series_uid: str
    slice_index: int
    window: WindowLevel | None
    inverted: bool

@dataclass(frozen=True, slots=True)
class RenderResult:
    response_id: str
    viewport_id: str
    series_uid: str
    image: np.ndarray | None
    modality_pixel: np.ndarray | None
    frame_meta: FrameDisplayMeta

@dataclass(frozen=True, slots=True)
class DicomLoadResult:
    window: WindowLevel
    inverted: bool
    image: np.ndarray | None
    modality_pixel: np.ndarray | None
    instance_meta: InstanceDisplayMeta

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

@dataclass(frozen=True, slots=True)
class PointerDisplayMeta:
    pointer_x: float | None
    pointer_y: float | None
    pointer_ct_value: float | None
