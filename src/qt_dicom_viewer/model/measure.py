from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import TypeAlias

from .dicom_types import ImageGeometryMeta
from .image_geometry import ImagePoint


class AnglePointIndex(IntEnum):
    START = 0
    VERTEX = 1
    END = 2


class LinePointIndex(IntEnum):
    START = 0
    END = 1


class MeasurementKind(StrEnum):
    LENGTH = "length"
    ANGLE = "angle"


class EditTargetKind(StrEnum):
    CONTROL_POINT = "controlPoint"
    SEGMENT = "segment"
    BODY = "body"
    LABEL = "label"


@dataclass(frozen=True, slots=True)
class MeasurementEditTarget:
    kind: EditTargetKind
    index: int | None = None


@dataclass(frozen=True, slots=True)
class MeasurementHit:
    measurement_id: str
    target: MeasurementEditTarget
    distance: float


@dataclass(slots=True)
class LengthMeasurementDraft:
    measurement_id: str
    series_uid: str
    sop_instance_uid: str
    slice_index: int
    points: list[ImagePoint]
    length_mm: float


@dataclass(slots=True)
class AngleMeasurementDraft:
    measurement_id: str
    series_uid: str
    sop_instance_uid: str
    slice_index: int
    points: list[ImagePoint]
    angle: float


MeasurementDraft: TypeAlias = (
    LengthMeasurementDraft
    | AngleMeasurementDraft
)


@dataclass(frozen=True, slots=True)
class LengthMeasurement:
    measurement_id: str
    series_uid: str
    sop_instance_uid: str
    slice_index: int
    points: tuple[ImagePoint, ...]
    length_mm: float


@dataclass(frozen=True, slots=True)
class AngleMeasurement:
    measurement_id: str
    series_uid: str
    sop_instance_uid: str
    slice_index: int
    points: tuple[ImagePoint, ...]
    angle: float


Measurement: TypeAlias = (
    LengthMeasurement
    | AngleMeasurement
)


@dataclass(frozen=True, slots=True)
class MeasureContext:
    measurement_kind: MeasurementKind
    series_uid: str
    sop_instance_uid: str
    slice_index: int
    geometry: ImageGeometryMeta
    endpoint_tolerance: float
    line_tolerance: float


@dataclass(slots=True)
class CreateMeasurementTransaction:
    context: MeasureContext
    draft: MeasurementDraft
    target: MeasurementEditTarget


@dataclass(slots=True)
class EditMeasurementTransaction:
    context: MeasureContext
    draft: MeasurementDraft
    target: MeasurementEditTarget


MeasurementTransaction: TypeAlias = (
    CreateMeasurementTransaction
    | EditMeasurementTransaction
)
