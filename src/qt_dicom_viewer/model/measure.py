from dataclasses import dataclass

from qt_dicom_viewer.model import  ImagePoint


@dataclass( slots=True)
class LengthMeasurementDraft:
    measurement_id: str
    series_uid: str
    sop_instance_uid: str
    slice_index: int
    start: ImagePoint
    end: ImagePoint
    length_mm: float


@dataclass(frozen=True, slots=True)
class LengthMeasurement:
    measurement_id: str
    series_uid: str
    sop_instance_uid: str
    slice_index: int
    start: ImagePoint
    end: ImagePoint
    length_mm: float
