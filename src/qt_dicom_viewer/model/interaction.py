from dataclasses import dataclass
from typing import TypeAlias

from .dicom_types import WindowLevel
from .measure import MeasureContext


@dataclass(frozen=True, slots=True)
class SliceIndexChange:
    slice_index: int


@dataclass(frozen=True, slots=True)
class WindowLevelChange:
    window: WindowLevel
    inverted: bool


@dataclass(frozen=True, slots=True)
class PanChange:
    offset_x: float
    offset_y: float


@dataclass(frozen=True, slots=True)
class ZoomChange:
    zoom: float


InteractionResult: TypeAlias = (
    SliceIndexChange
    | WindowLevelChange
    | PanChange
    | ZoomChange
)


@dataclass(frozen=True, slots=True)
class WindowLevelContext:
    viewport_size: tuple[float, float]
    inverted: bool
    current_window: WindowLevel | None


@dataclass(frozen=True, slots=True)
class ScrollContext:
    slice_index: int
    slice_count: int


@dataclass(frozen=True, slots=True)
class PanContext:
    current_pan_x: float
    current_pan_y: float


@dataclass(frozen=True, slots=True)
class ZoomContext:
    viewport_size: tuple[float, float]
    current_zoom: float


OperationStartContext: TypeAlias = (
    WindowLevelContext
    | ScrollContext
    | PanContext
    | ZoomContext
    | MeasureContext
)
