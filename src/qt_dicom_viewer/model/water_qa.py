"""Single-slice water phantom geometry and measured (not graded) QA results."""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WaterPhantom:
    column: float
    row: float
    radius_mm: float
    boundary_coverage: float


@dataclass(frozen=True, slots=True)
class WaterQaSettings:
    roi_diameter_mm: float = 20.0
    edge_clearance_mm: float = 20.0


@dataclass(frozen=True, slots=True)
class WaterQaRoi:
    key: str
    label: str
    column: float
    row: float
    radius_mm: float
    pixel_count: int
    area_mm2: float
    mean_hu: float
    std_hu: float
    minimum_hu: float
    maximum_hu: float
    delta_center_hu: float


@dataclass(frozen=True, slots=True)
class WaterQaResult:
    phantom: WaterPhantom
    settings: WaterQaSettings
    rois: tuple[WaterQaRoi, ...]
    water_ct_hu: float
    noise_hu: float
    uniformity_hu: float
    consistency_range_hu: float
    horizontal_difference_hu: float
    vertical_difference_hu: float
    noise_range_hu: float
