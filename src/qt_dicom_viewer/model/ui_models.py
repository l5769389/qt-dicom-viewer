from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import List

from qt_dicom_viewer.model import WindowLevel, ToolType


@dataclass(frozen=True, slots=True)
class DisplayStyle:
    color_map: str = "grayscale"
    no_data_color: str = "#000000"


class ViewportTransformAction(StrEnum):
    ROTATE_CLOCKWISE_90 = "rotate:cw90"
    ROTATE_COUNTERCLOCKWISE_90 = "rotate:ccw90"
    MIRROR_HORIZONTAL = "rotate:mirror-h"
    MIRROR_VERTICAL = "rotate:mirror-v"


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
    dicom_file_count: int
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
    inverted: bool = False
    display_style: DisplayStyle = field(
        default_factory=DisplayStyle
    )


@dataclass(frozen=True, slots=True)
class TabConfig:
    tab_id: str
    tab_label: str
    tab_type: str
    series_metas: tuple[SeriesDisplayMeta, ...]



class ToolBehavior(StrEnum):
    INTERACTION = "interaction" # 只触发长期功能
    PANEL = "panel"    # 只打开面板
    INTERACTION_PANEL = "interactionPanel" # 触发长期功能且打开面板
    COMMAND = "command"  # 一次性命令，比如reset


class ToolPanelType(StrEnum):
    ANNOTATE = 'annotate'
    NONE = ""
    WINDOW = "window"
    ROTATE = "rotate"
    EXPORT = "export"
    SCROLL = "scroll"
    PAN = "pan"
    ZOOM = "zoom"
    MEASURE = "measure"


class InteractionType(StrEnum):
    NONE = ""
    WINDOW = "window"
    SCROLL = "scroll"
    PAN = "pan"
    ZOOM = "zoom"
    MEASURE_LENGTH = "measure:length"
    MEASURE_ANGLE = "measure:angle"
    MEASURE_RECT = "measure:rect"
    MEASURE_ELLIPSE = "measure:ellipse"

    ROTATE_CW90 = "rotate:cw90"
    ROTATE_CCW90 = "rotate:ccw90"
    ROTATE_flip_hor = "rotate:flip_h"
    ROTATE_flip_ver = "rotate:flip_v"

@dataclass(frozen=True, slots=True)
class ToolDefinition:
    behavior: ToolBehavior  # 行为：是打开面板、还是发送命令 还是启用长期功能
    interaction_tool: InteractionType | None = None # 启用的长期功能
    panel: ToolPanelType = ToolPanelType.NONE  # 打开的面板
    command: str | None = None  # 发送命令


TOOL_DEFINITIONS: dict[ToolType, ToolDefinition] = {
    ToolType.WINDOW: ToolDefinition(
        behavior=ToolBehavior.INTERACTION_PANEL,
        interaction_tool=InteractionType.WINDOW,
        panel=ToolPanelType.WINDOW,
    ),
    ToolType.SCROLL: ToolDefinition(
        behavior=ToolBehavior.INTERACTION,
        interaction_tool=InteractionType.SCROLL,
    ),
    ToolType.PAN: ToolDefinition(
        behavior=ToolBehavior.INTERACTION,
        interaction_tool=InteractionType.PAN,
    ),
    ToolType.ZOOM: ToolDefinition(
        behavior=ToolBehavior.INTERACTION,
        interaction_tool=InteractionType.ZOOM,
    ),
    ToolType.ROTATE: ToolDefinition(
        behavior=ToolBehavior.PANEL,
        panel=ToolPanelType.ROTATE,
    ),
    ToolType.ANNOTATE: ToolDefinition(
        behavior=ToolBehavior.PANEL,
        panel=ToolPanelType.ANNOTATE,
    ),
    ToolType.RESET: ToolDefinition(
        behavior=ToolBehavior.COMMAND,
        command="viewport:reset",
    ),
}

@dataclass(frozen=True, slots=True)
class WindowPreset:
    preset_id: str
    label: str
    center: float
    width: float
    modality: str = "CT"
