"""Serializable 3D display data, independent of Qt and VTK objects."""
from dataclasses import dataclass
from enum import StrEnum

from .dicom_types import WindowLevel


class VolumeBlendMode(StrEnum):
    COMPOSITE = "composite"
    MIP = "mip"
    ADDITIVE = "additive"


@dataclass(frozen=True, slots=True)
class VolumePreset:
    preset_id: str
    label: str
    group: str
    # Transfer points use normalized window coordinates; RGB/opacity are 0..1.
    colors: tuple[tuple[float, float, float, float], ...]
    opacity: tuple[tuple[float, float], ...]
    default_window: WindowLevel | None = None  # None uses the series default.
    ct_only: bool = False
    blend_mode: VolumeBlendMode = VolumeBlendMode.COMPOSITE
    shade: bool = True
    ambient: float = 0.3
    diffuse: float = 0.7
    specular: float = 0.15
    specular_power: float = 10.0
    opacity_unit_distance: float = 1.0


@dataclass(frozen=True, slots=True)
class VolumeDisplayState:
    preset_id: str = "general"
    window: WindowLevel | None = None


@dataclass(frozen=True, slots=True)
class VolumeDirection:
    face: str
    label: str
    normal: tuple[float, float, float]
    up: tuple[float, float, float]
    color: str


# Normals are in patient LPS, shared by the camera, cube and QML controls.
VOLUME_DIRECTIONS = (
    VolumeDirection("A", "前 A", (0, -1, 0), (0, 0, 1), "#269967"),
    VolumeDirection("P", "后 P", (0, 1, 0), (0, 0, 1), "#218f9f"),
    VolumeDirection("L", "左 L", (1, 0, 0), (0, 0, 1), "#c64f52"),
    VolumeDirection("R", "右 R", (-1, 0, 0), (0, 0, 1), "#b96b26"),
    VolumeDirection("S", "上 S", (0, 0, 1), (0, -1, 0), "#427acb"),
    VolumeDirection("I", "下 I", (0, 0, -1), (0, -1, 0), "#8c5ec0"),
)
