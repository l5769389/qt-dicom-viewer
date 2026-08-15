from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
from enum import StrEnum

import numpy as np


@dataclass(frozen=True)
class DicomInstanceMeta:
    path: Path
    patient_name: str
    patient_id: str
    study_description: str
    study_instance_uid: str
    series_description: str
    series_instance_uid: str
    series_number: int | None
    instance_number: int | None
    modality: str
    rows: int | None
    columns: int | None
    transfer_syntax: str


@dataclass(frozen=True)
class DicomSeriesSummary:
    patient_name: str
    patient_id: str
    study_description: str
    study_instance_uid: str
    series_description: str
    series_instance_uid: str
    series_number: int | None
    modality: str
    file_count: int
    first_file: Path
    rows: int | None
    columns: int | None
    ordered_file_paths: List[Path] | None

    @property
    def display_name(self) -> str:
        parts: list[str] = []

        if self.series_number is not None:
            parts.append(f"Series {self.series_number}")

        if self.series_description:
            parts.append(self.series_description)

        if self.modality:
            parts.append(self.modality)

        return " / ".join(parts) or "Unnamed Series"


@dataclass(frozen=True)
class DicomFolderScanResult:
    folder: Path
    total_file_count: int
    dicom_file_count: int
    skipped_file_count: int
    series: list[DicomSeriesSummary]


@dataclass(frozen=True)
class DicomFolderScanSnapshot:
    folder: Path
    total_file_count: int
    dicom_file_count: int
    skipped_file_count: int
    series: list[DicomSeriesSummary]

@dataclass(frozen=True, slots=True)
class SeriesDisplayMeta:
    patient_name: str
    patient_id: str
    study_description: str
    series_description: str
    modality: str
    series_uid: str


@dataclass(frozen=True, slots=True)
class ViewportConfig:
    viewport_id: str
    tab_id: str
    viewport_type: str
    series_uid: str
    series_meta: SeriesDisplayMeta

@dataclass(frozen=True)
class ViewportState:
    slice_index: int = 0
    slice_count: int = 0
    window: WindowLevel | None = None
    width: float = 1.0
    height: float = 0
    zoom: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0
    rotation_degrees: float = 0.0
    horizontal_flip: bool = False
    vertical_flip: bool = False


@dataclass(frozen=True, slots=True)
class TabConfig:
    tab_id: str
    tab_label: str
    tab_type: str
    series_metas: tuple[SeriesDisplayMeta, ...]


class TabType(StrEnum):
    TWO_D = "2d"
    MPR = "mpr"


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

@dataclass(frozen=True, slots=True)
class RenderResult:
    response_id: str
    viewport_id: str
    series_uid: str
    image: np.ndarray | None
    frame_meta: FrameDisplayMeta


@dataclass(frozen=True, slots=True)
class DicomLoadResult:
    window: WindowLevel
    image: np.ndarray | None
    instance_meta: InstanceDisplayMeta


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
    instance_meta: InstanceDisplayMeta
