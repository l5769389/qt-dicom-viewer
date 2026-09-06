from __future__ import annotations

from dataclasses import dataclass

import numpy as np

@dataclass(frozen=True, slots=True)
class WindowLevel:
    center: float
    width: float


@dataclass(frozen=True, slots=True)
class PixelUnitOption:
    """One truthful display/measurement unit derived from source pixels."""

    unit_id: str
    label: str
    unit: str
    scale_from_source: float
    available: bool = True
    warning: str | None = None


@dataclass(frozen=True, slots=True)
class PixelValueMeta:
    """Describe the real-world values exposed by one rendered frame."""

    unit: str = ""
    suv_type: str | None = None
    source_unit: str | None = None
    quantification: str = "native"
    warning: str | None = None
    unit_id: str = "native"
    scale_from_source: float = 1.0
    unit_options: tuple[PixelUnitOption, ...] = ()

    @property
    def is_suv(self) -> bool:
        return self.unit.casefold().startswith("suv")


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
    radiopharmaceutical: str | None = None
    pet_units: str | None = None
    suv_type: str | None = None
    decay_correction: str | None = None
    corrected_image: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FrameDisplayMeta:
    slice_index: int
    slice_count: int
    window: WindowLevel
    inverted: bool
    instance_meta: InstanceDisplayMeta
    geometry: ImageGeometryMeta
    pixel_value_meta: PixelValueMeta = PixelValueMeta()


@dataclass(frozen=True, slots=True)
class PointerDisplayMeta:
    pointer_x: float | None
    pointer_y: float | None
    pointer_value: float | None


@dataclass(frozen=True, slots=True)
class DicomLoadResult:
    window: WindowLevel
    inverted: bool
    image: np.ndarray | None
    modality_pixel: np.ndarray | None
    instance_meta: InstanceDisplayMeta
    pixel_value_meta: PixelValueMeta = PixelValueMeta()
