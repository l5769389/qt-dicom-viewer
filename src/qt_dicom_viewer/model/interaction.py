from dataclasses import dataclass
from typing import TypeAlias, Tuple

from qt_dicom_viewer.model import WindowLevel


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
    viewport_size: Tuple[float, float]
    inverted: bool
    current_window: WindowLevel | None

@dataclass(frozen=True, slots=True)
class ScrollContext:
    slice_index: int
    slice_count: int

OperationStartContext:TypeAlias = (
    WindowLevelContext
    | ScrollContext
)
