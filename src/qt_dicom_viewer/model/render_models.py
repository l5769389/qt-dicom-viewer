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
)
from .dicom_models import ViewportType, MprPlane, TwoDViewType
from .dicom_types import FrameDisplayMeta, WindowLevel

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
    view_roll_radians: float = 0.0
    mpr_grid: MprGridSpec | None = None
    mpr_grid_anchor: MprGridAnchor | None = None

    @property
    def view_type(self) -> ViewportType:
        return self.plane


RenderRequest: TypeAlias = (
    StackRenderRequest
    | MprRenderRequest
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
    mpr_view_grids: MprViewGrids | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class StackRenderResult(_RenderResultBase):
    ...


RenderResult: TypeAlias = (
    StackRenderResult
    | MprRenderResult
)


@dataclass(frozen=True, slots=True, kw_only=True)
class RenderFailure:
    request_id: str
    viewport_id: str
    error: Exception
