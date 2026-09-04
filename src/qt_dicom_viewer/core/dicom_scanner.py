import os
import re
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Iterable, Iterator, cast

import pydicom

from qt_dicom_viewer.model import (
    DicomFolderScanSnapshot,
    DicomInstanceMeta,
    DicomPhaseRecord,
    DicomSeriesRecord,
    PixelSpacing,
)
from qt_dicom_viewer.utils.utils import (
    _as_float,
    _as_float_tuple,
    _as_int,
    _as_str,
    _transfer_syntax_name,
)


# Ordered from explicit temporal identifiers to cautious acquisition-time
# fallbacks. Cross-series geometry validation is required for every source.
_PHASE_VALUE_KEYWORDS: tuple[str, ...] = (
    "TemporalPositionIdentifier",
    "TemporalPositionIndex",
    "PhaseNumber",
    "FrameAcquisitionNumber",
    "NominalPercentageOfCardiacPhase",
    "NominalPercentageOfRespiratoryPhase",
    "RespiratoryCyclePosition",
    "CardiacCyclePosition",
    "TemporalPositionTimeOffset",
    "TriggerTime",
    "ImageTriggerDelay",
    "TriggerTimeOffset",
    "NominalCardiacTriggerDelayTime",
    "NominalCardiacTriggerTimePriorToRPeak",
    "ActualCardiacTriggerTimePriorToRPeak",
    "ActualCardiacTriggerDelayTime",
    "NominalRespiratoryTriggerDelayTime",
    "ActualRespiratoryTriggerDelayTime",
    "FrameReferenceTime",
    "PhaseDelay",
    "PhaseDescription",
    "AcquisitionNumber",
    "FrameAcquisitionDateTime",
    "AcquisitionDateTime",
    "AcquisitionTime",
    "ContentTime",
)

_INTEGER_PHASE_KEYWORDS = frozenset({
    "TemporalPositionIdentifier",
    "TemporalPositionIndex",
    "PhaseNumber",
    "FrameAcquisitionNumber",
    "PhaseDelay",
    "AcquisitionNumber",
})
_TEXT_PHASE_KEYWORDS = frozenset({
    "RespiratoryCyclePosition",
    "CardiacCyclePosition",
    "PhaseDescription",
    "FrameAcquisitionDateTime",
    "AcquisitionDateTime",
    "AcquisitionTime",
    "ContentTime",
})

_SERIES_DESCRIPTION_PHASE_PATTERN = re.compile(
    r"^(?P<base>.+?)[\s_-]*(?:phase|ph)[\s_-]*"
    r"(?P<value>\d+(?:\.\d+)?)(?:\s*%)?$",
    re.IGNORECASE,
)


def _optional_str(value: object) -> str | None:
    text = _as_str(value).strip()
    return text or None


def _read_phase_values(
    dataset: pydicom.dataset.Dataset,
) -> tuple[tuple[str, int | float | str], ...]:
    values: list[tuple[str, int | float | str]] = []
    for keyword in _PHASE_VALUE_KEYWORDS:
        raw_value = getattr(dataset, keyword, None)
        if keyword in _INTEGER_PHASE_KEYWORDS:
            value = _as_int(raw_value)
        elif keyword in _TEXT_PHASE_KEYWORDS:
            value = _optional_str(raw_value)
        else:
            value = _as_float(raw_value)
        if value is not None:
            values.append((keyword, value))
    return tuple(values)


def _iter_visible_files(folder: Path):
    for root, dirnames, filenames in os.walk(folder):
            # dirnames 和 os.walk(folder) 返回的对象指向同一块区域。
            # 如果采用 dirnames = xxx 。则下次遍历还会遍历.xx的文件夹。
            dirnames[:] = sorted(name for name in dirnames if not name.startswith("."))
            for filename in sorted(filenames):
                if filename.startswith("."):
                    continue
                yield Path(root) / filename


def _read_instance(file_path: Path) -> DicomInstanceMeta | None:
    try:
        dataset = pydicom.dcmread(file_path, stop_before_pixels=True)
    except Exception:
        return None

    study_uid = _as_str(getattr(dataset, "StudyInstanceUID", ""))
    series_uid = _as_str(getattr(dataset, "SeriesInstanceUID", ""))
    sop_instance_uid = _as_str(getattr(dataset, "SOPInstanceUID", ""))

    if not series_uid or not sop_instance_uid:
        return None

    image_position = _as_float_tuple(
        getattr(dataset, "ImagePositionPatient", None),
        expected_length=3,
    )
    image_orientation = _as_float_tuple(
        getattr(dataset, "ImageOrientationPatient", None),
        expected_length=6,
    )
    spacing_values = _as_float_tuple(
        getattr(dataset, "PixelSpacing", None),
        expected_length=2,
    )

    pixel_spacing = None
    if spacing_values is not None:
        row_spacing, column_spacing = spacing_values
        if row_spacing > 0 and column_spacing > 0:
            pixel_spacing = PixelSpacing(
                row=row_spacing,
                column=column_spacing,
            )

    return DicomInstanceMeta(
        path=file_path,
        patient_name=_as_str(getattr(dataset, "PatientName", "")),
        patient_id=_as_str(getattr(dataset, "PatientID", "")),
        study_description=_as_str(getattr(dataset, "StudyDescription", "")),
        study_instance_uid=study_uid,
        series_description=_as_str(getattr(dataset, "SeriesDescription", "")),
        series_instance_uid=series_uid,
        series_number=_as_int(getattr(dataset, "SeriesNumber", None)),
        instance_number=_as_int(getattr(dataset, "InstanceNumber", None)),
        modality=_as_str(getattr(dataset, "Modality", "")),
        rows=_as_int(getattr(dataset, "Rows", None)),
        columns=_as_int(getattr(dataset, "Columns", None)),
        transfer_syntax=_transfer_syntax_name(dataset),
        sop_instance_uid=sop_instance_uid,
        image_orientation_patient=cast(
            tuple[float, float, float, float, float, float] | None,
            image_orientation,
        ),
        image_position_patient=cast(
            tuple[float, float, float] | None,
            image_position,
        ),
        pixel_spacing=pixel_spacing,
        slice_thickness=_as_float(getattr(dataset, "SliceThickness", None)),
        frame_of_reference_uid=_as_str(
            getattr(dataset, "FrameOfReferenceUID", "")
        ),
        phase_values=_read_phase_values(dataset),
        number_of_temporal_positions=_as_int(
            getattr(dataset, "NumberOfTemporalPositions", None)
        ),
        number_of_phases=_as_int(getattr(dataset, "NumberOfPhases", None)),
        number_of_frames=(
            _as_int(getattr(dataset, "NumberOfFrames", None)) or 1
        ),
    )


def _build_series_record(
    instances: list[DicomInstanceMeta]
) -> DicomSeriesRecord:
    ordered = tuple(sorted(instances, key=_instance_sort_key))
    first = ordered[0]

    return DicomSeriesRecord(
        patient_name=first.patient_name,
        patient_id=first.patient_id,
        study_description=first.study_description,
        study_instance_uid=first.study_instance_uid,
        series_description=first.series_description,
        series_instance_uid=first.series_instance_uid,
        series_number=first.series_number,
        modality=first.modality,
        instances=ordered,
        frame_of_reference_uid=first.frame_of_reference_uid,
    )


def _ordered_phase_values(
    source_keyword: str,
    phase_values: Iterable[int | float | str],
) -> list[int | float | str]:
    values = list(phase_values)
    if all(isinstance(value, (int, float)) for value in values):
        return sorted(values, key=float)
    if source_keyword in {
        "FrameAcquisitionDateTime",
        "AcquisitionDateTime",
        "AcquisitionTime",
        "ContentTime",
    }:
        return sorted(values, key=str)
    return values


def _instance_geometry_signature(
    instance: DicomInstanceMeta,
) -> tuple[object, ...] | None:
    position = instance.image_position_patient
    orientation = instance.image_orientation_patient
    spacing = instance.pixel_spacing
    if (
        instance.rows is None
        or instance.columns is None
        or position is None
        or orientation is None
        or spacing is None
    ):
        return None

    return (
        instance.rows,
        instance.columns,
        *(round(value, 4) for value in position),
        *(round(value, 6) for value in orientation),
        round(spacing.row, 6),
        round(spacing.column, 6),
    )


def _link_cross_series_phases(
    series_records: list[DicomSeriesRecord],
) -> list[DicomSeriesRecord]:
    records_by_uid = {
        series.series_instance_uid: series
        for series in series_records
    }
    linked_uids: set[str] = set()
    candidate_sources = (
        *_PHASE_VALUE_KEYWORDS,
        "SeriesDescriptionPhaseSuffix",
    )
    for source_keyword in candidate_sources:
        groups: dict[
            tuple[str, str, str, str, int],
            list[tuple[int | float | str, DicomSeriesRecord]],
        ] = defaultdict(list)

        for original_series in series_records:
            series_uid = original_series.series_instance_uid
            if series_uid in linked_uids:
                continue

            marker = _cross_series_phase_marker(
                original_series,
                source_keyword=source_keyword,
            )
            if marker is None:
                continue
            phase_value, description_base = marker

            groups[
                (
                    original_series.study_instance_uid,
                    original_series.frame_of_reference_uid,
                    original_series.modality,
                    description_base.casefold(),
                    len(original_series.instances),
                )
            ].append((phase_value, original_series))

        for group_key, candidate_series in groups.items():
            if len(candidate_series) < 2:
                continue

            geometry_groups: dict[
                tuple[tuple[object, ...], ...],
                list[tuple[int | float | str, DicomSeriesRecord]],
            ] = defaultdict(list)
            for phase_value, original_series in candidate_series:
                geometry = _series_geometry_signature(original_series)
                if geometry is not None:
                    geometry_groups[geometry].append(
                        (phase_value, original_series)
                    )

            for phase_series in geometry_groups.values():
                if len(phase_series) < 2:
                    continue
                _apply_cross_series_group(
                    phase_series=phase_series,
                    source_keyword=source_keyword,
                    records_by_uid=records_by_uid,
                    linked_uids=linked_uids,
                )

    return [
        records_by_uid[series.series_instance_uid]
        for series in series_records
    ]


def _apply_cross_series_group(
    *,
    phase_series: list[tuple[int | float | str, DicomSeriesRecord]],
    source_keyword: str,
    records_by_uid: dict[str, DicomSeriesRecord],
    linked_uids: set[str],
) -> None:
    series_by_value = {
        phase_value: series
        for phase_value, series in phase_series
    }
    if len(series_by_value) != len(phase_series):
        return
    if not _matches_expected_phase_count(
        tuple(series_by_value.values())
    ):
        return

    source_values = _ordered_phase_values(
        source_keyword,
        series_by_value,
    )
    phase_identifiers = {
        source_value: (
            source_value
            if isinstance(source_value, int)
            else index
        )
        for index, source_value in enumerate(
            source_values,
            start=1,
        )
    }
    phases = tuple(
        DicomPhaseRecord(
            phase_identifier=phase_identifiers[source_value],
            instances=series_by_value[source_value].instances,
        )
        for source_value in source_values
    )
    for _, original_series in phase_series:
        series_uid = original_series.series_instance_uid
        records_by_uid[series_uid] = replace(
            original_series,
            phases=phases,
            phase_source_keyword=source_keyword,
        )
        linked_uids.add(series_uid)


def _cross_series_phase_marker(
    series: DicomSeriesRecord,
    *,
    source_keyword: str,
) -> tuple[int | float | str, str] | None:
    description_marker = _series_description_phase_marker(
        series.series_description
    )
    if source_keyword == "SeriesDescriptionPhaseSuffix":
        return description_marker

    source_values: set[int | float | str] = set()
    for instance in series.instances:
        source_value = instance.phase_value(source_keyword)
        if source_value is None:
            return None
        if isinstance(source_value, float):
            source_value = round(source_value, 6)
        source_values.add(source_value)
        if len(source_values) > 1:
            return None

    if not source_values:
        return None
    description_base = (
        description_marker[1]
        if description_marker is not None
        else series.series_description.strip()
    )
    if not description_base:
        return None
    return next(iter(source_values)), description_base


def _series_description_phase_marker(
    series_description: str,
) -> tuple[int | float, str] | None:
    match = _SERIES_DESCRIPTION_PHASE_PATTERN.fullmatch(
        series_description.strip()
    )
    if match is None:
        return None

    description_base = match.group("base").rstrip(" _-")
    if not description_base:
        return None
    raw_value = match.group("value")
    phase_value: int | float = (
        int(raw_value)
        if "." not in raw_value
        else round(float(raw_value), 6)
    )
    return phase_value, description_base


def _series_geometry_signature(
    series: DicomSeriesRecord,
) -> tuple[tuple[object, ...], ...] | None:
    if len(series.instances) < 2 or any(
        instance.number_of_frames != 1
        for instance in series.instances
    ):
        return None
    signature = tuple(
        _instance_geometry_signature(instance)
        for instance in series.instances
    )
    if any(item is None for item in signature):
        return None
    if len(set(signature)) != len(signature):
        return None
    return cast(tuple[tuple[object, ...], ...], signature)


def _matches_expected_phase_count(
    series_records: tuple[DicomSeriesRecord, ...],
) -> bool:
    expected_counts = {
        expected_count
        for series in series_records
        for instance in series.instances
        for expected_count in (
            instance.number_of_temporal_positions,
            instance.number_of_phases,
        )
        if expected_count is not None
    }
    return (
        len(expected_counts) <= 1
        and (
            not expected_counts
            or next(iter(expected_counts)) == len(series_records)
        )
    )



def _build_series_from_map(
    series_map: dict[tuple[str, str], list[DicomInstanceMeta]],
    *,
    link_cross_series: bool = True,
) -> list[DicomSeriesRecord]:
    series = [
        _build_series_record(series_instances)
        for series_instances in series_map.values()
    ]
    return (
        _link_cross_series_phases(series)
        if link_cross_series
        else series
    )

class DicomFolderScanner:
    def scan(self,folder_path) -> Iterator[DicomFolderScanSnapshot]:
        folder = Path(folder_path).expanduser()
        if not folder.exists():
            raise FileNotFoundError(f"Folder does not exist: {folder}")

        if not folder.is_dir():
            raise NotADirectoryError(f"Path is not a folder: {folder}")

        total_file_count = 0
        skipped_file_count = 0
        series_map: dict[tuple[str, str],list[DicomInstanceMeta]] = defaultdict(list)
        instances: list[DicomInstanceMeta] = []
        for file_path in _iter_visible_files(folder_path):
            total_file_count += 1
            instance = _read_instance(file_path)

            if instance is None:
                skipped_file_count += 1
            else:
                instances.append(instance)

                key = (
                    instance.study_instance_uid,
                    instance.series_instance_uid,
                )

                series_map[key].append(instance)

            yield DicomFolderScanSnapshot(
                folder=folder,
                total_file_count=total_file_count,
                dicom_file_count=len(instances),
                skipped_file_count=total_file_count - len(instances),
                series=_build_series_from_map(
                    series_map,
                    link_cross_series=False,
                ),
            )

        yield DicomFolderScanSnapshot(
            folder=folder,
            total_file_count=total_file_count,
            dicom_file_count=len(instances),
            skipped_file_count=total_file_count - len(instances),
            series=_build_series_from_map(series_map),
        )

def _instance_sort_key(
    instance: DicomInstanceMeta,
) -> tuple[int, float, int, str]:
    instance_number = (
        instance.instance_number if instance.instance_number is not None else 1_000_000
    )
    orientation = instance.image_orientation_patient
    position = instance.image_position_patient

    if orientation is not None and position is not None:
        row_x, row_y, row_z, column_x, column_y, column_z = orientation
        normal = (
            row_y * column_z - row_z * column_y,
            row_z * column_x - row_x * column_z,
            row_x * column_y - row_y * column_x,
        )
        spatial_position = sum(
            normal_component * position_component
            for normal_component, position_component in zip(normal, position)
        )
        return 0, spatial_position, instance_number, str(instance.path)

    return 1, float(instance_number), instance_number, str(instance.path)


def _series_sort_key(series: DicomSeriesRecord) -> tuple[str, str, int, str, str]:
    series_number = series.series_number if series.series_number is not None else 1_000_000
    return (
        series.patient_name,
        series.study_description,
        series_number,
        series.series_description,
        series.series_instance_uid,
    )
