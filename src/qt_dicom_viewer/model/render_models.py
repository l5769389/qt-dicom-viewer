from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np

from .dicom_core import (
    MprFrame,
    MprGridAnchor,
    MprGridSpec,
    MprImageGeometry,
    MprViewGrids,
    DicomVolume,
)
from .dicom_models import (
    MprPlane,
    MprProjectionMode,
    TwoDViewType,
    ViewportType,
)
from .dicom_types import FrameDisplayMeta, WindowLevel


@dataclass(frozen=True, slots=True, kw_only=True)
class VolumeLoadRequest:
    request_id: str
    viewport_id: str
    series_uid: str


@dataclass(frozen=True, slots=True, kw_only=True)
class VolumeLoadResult:
    response_id: str
    viewport_id: str
    series_uid: str
    volume: DicomVolume

# 为什么基础类使用 kw_only=True
# 这样所有字段都必须显式按名称传递：
# kw_only=True 还能避免 dataclass 继承时常见的字段顺序问题，例如基础类有默认值，而子类又添加没有默认值的字段。
@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class _RenderRequestBase:
    request_id: str
    viewport_id: str
    series_uid: str
    window: WindowLevel | None
    inverted: bool
    color_map: str = "grayscale"


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class StackRenderRequest(_RenderRequestBase):
    slice_index: int

    @property
    def view_type(self) -> ViewportType:
        return TwoDViewType.STACK


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class MprRenderRequest(_RenderRequestBase):
    plane: MprPlane
    mpr_frame: MprFrame | None
    phase_identifier: int | None = None
    view_roll_radians: float = 0.0
    mpr_grid: MprGridSpec | None = None
    mpr_grid_anchor: MprGridAnchor | None = None
    projection_mode: MprProjectionMode | None = None
    slab_thickness_mm: float = 0.0

    @property
    def view_type(self) -> ViewportType:
        return self.plane


RenderRequest: TypeAlias = (
    StackRenderRequest
    | MprRenderRequest
    | VolumeLoadRequest
)


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class _RenderResultBase:
    response_id: str
    viewport_id: str
    series_uid: str
    view_type: ViewportType
    image: np.ndarray | None
    modality_pixel: np.ndarray | None
    frame_meta: FrameDisplayMeta


@dataclass(frozen=True, slots=True, kw_only=True)
class MprRenderResult(_RenderResultBase):
    mpr_frame: MprFrame | None
    plane_geometry: MprImageGeometry | None
    phase_identifier: int | None = None
    mpr_view_grids: MprViewGrids | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class StackRenderResult(_RenderResultBase):
    ...


RenderResult: TypeAlias = (
    StackRenderResult
    | MprRenderResult
    | VolumeLoadResult
)


@dataclass(frozen=True, slots=True, kw_only=True)
class RenderFailure:
    request_id: str
    viewport_id: str
    error: Exception
