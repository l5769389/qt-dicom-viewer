from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from .dicom_models import TabType, ViewportType
from .dicom_types import PixelSpacing, WindowLevel


@dataclass(frozen=True, slots=True)
class DisplayStyle:
    color_map: str = "grayscale"
    no_data_color: str = "#000000"


class ViewportTransformAction(StrEnum):
    ROTATE_CLOCKWISE_90 = "rotate:cw90"
    ROTATE_COUNTERCLOCKWISE_90 = "rotate:ccw90"
    MIRROR_HORIZONTAL = "rotate:mirror-h"
    MIRROR_VERTICAL = "rotate:mirror-v"


@dataclass(frozen=True, slots=True)
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
    sop_instance_uid: str
    pixel_spacing: PixelSpacing | None
    modality: str
    rows: int | None
    columns: int | None
    transfer_syntax: str
    image_position_patient: (
        tuple[float, float, float] | None
    )
    image_orientation_patient: (
        tuple[float, float, float, float, float, float]
        | None
    )
    slice_thickness: float | None

@dataclass(frozen=True, slots=True)
class DicomSeriesRecord:
    patient_name: str
    patient_id: str
    study_description: str
    study_instance_uid: str
    series_description: str
    series_instance_uid: str
    series_number: int | None
    modality: str
    instances: tuple[DicomInstanceMeta, ...]

    @property
    def dicom_file_count(self) -> int:
        return len(self.instances)

    @property
    def first_file(self) -> Path | None:
        return self.instances[0].path if self.instances else None

    @property
    def rows(self) -> int | None:
        return self.instances[0].rows if self.instances else None

    @property
    def columns(self) -> int | None:
        return self.instances[0].columns if self.instances else None

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
    series: list[DicomSeriesRecord]


@dataclass(frozen=True)
class DicomFolderScanSnapshot:
    folder: Path
    total_file_count: int
    dicom_file_count: int
    skipped_file_count: int
    series: list[DicomSeriesRecord]

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
    viewport_type: ViewportType
    series_uid: str
    series_meta: SeriesDisplayMeta

@dataclass(frozen=True)
class ViewportState:
    slice_index: int | None # None为了mpr请求的时候能够直接被设置为居中位置。
    slice_count: int | None
    window: WindowLevel | None = None
    width: float = 1.0
    height: float = 0
    zoom: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0
    rotation_degrees: float = 0.0
    horizontal_flip: bool = False
    vertical_flip: bool = False
    inverted: bool = False
    display_style: DisplayStyle = field(
        default_factory=DisplayStyle
    )


@dataclass(frozen=True, slots=True)
class TabConfig:
    tab_id: str
    tab_label: str
    tab_type: TabType
    series_metas: tuple[SeriesDisplayMeta, ...]


class ToolBehavior(StrEnum):
    INTERACTION = "interaction" # 只触发长期功能
    PANEL = "panel"    # 只打开面板
    INTERACTION_PANEL = "interactionPanel" # 触发长期功能且打开面板
    COMMAND = "command"  # 一次性命令，比如reset


class InteractionType(StrEnum):
    SERVICE_MTF = "service:mtf"
    NONE = ""
    WINDOW = "window"
    SCROLL = "scroll"
    PAN = "pan"
    ZOOM = "zoom"
    MEASURE_LENGTH = "measure:length"
    MEASURE_ANGLE = "measure:angle"
    MEASURE_RECT = "measure:rect"
    MEASURE_ELLIPSE = "measure:ellipse"
    MPR_ROTATE_3D = "mpr:rotate3d"

@dataclass(frozen=True, slots=True)
class WindowPreset:
    preset_id: str
    label: str
    center: float
    width: float
    modality: str = "CT"


@dataclass(frozen=True, slots=True)
class CrosshairColor:
    horizontal: str
    vertical: str


@dataclass(frozen=True, slots=True)
class CrosshairStyle:
    color: CrosshairColor
    centerGap: int = 14
    lineWidth: int= 1
