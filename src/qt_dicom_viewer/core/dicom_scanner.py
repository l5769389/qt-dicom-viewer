import os
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import pydicom

from qt_dicom_viewer.model import  DicomInstanceMeta, DicomSeriesSummary, \
    DicomFolderScanSnapshot
from qt_dicom_viewer.utils.utils import _as_str, _as_int, _transfer_syntax_name


def _iter_visible_files(folder: Path):
    for root, dirnames, filenames in os.walk(folder):
            # dirnames 和 os.walk(folder) 返回的对象指向同一块区域。
            # 如果采用 dirnames = xxx 。则下次遍历还会遍历.xx的文件夹。
            dirnames[:] = sorted(name for name in dirnames if not name.startswith("."))
            for filename in sorted(filenames):
                if filename.startswith("."):
                    continue
                yield Path(root) / filename


def _read_instance(file_path) -> DicomInstanceMeta | None:
    try:
        dataset = pydicom.dcmread(file_path, stop_before_pixels=True)
    except Exception as e:
        return None
    study_uid = _as_str(getattr(dataset, "StudyInstanceUID", ""))
    series_uid = _as_str(getattr(dataset, "SeriesInstanceUID", ""))

    if not study_uid and not series_uid:
        return None

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
    )


def _summarize_series(
        instances: list[DicomInstanceMeta]
) -> DicomSeriesSummary:
    ordered = sorted(instances, key=_instance_sort_key)
    first = ordered[0]

    return DicomSeriesSummary(
        patient_name=first.patient_name,
        patient_id=first.patient_id,
        study_description=first.study_description,
        study_instance_uid=first.study_instance_uid,
        series_description=first.series_description,
        series_instance_uid=first.series_instance_uid,
        series_number=first.series_number,
        modality=first.modality,
        dicom_file_count=len(ordered),
        first_file=first.path,
        ordered_file_paths = [file.path for file in ordered],
        rows=first.rows,
        columns=first.columns,
    )



def _build_series_from_map(series_map : dict[tuple[str, str], list[DicomInstanceMeta]]):
    return [
        _summarize_series(series_instances)
        for series_instances in series_map.values()
    ]

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
                series=_build_series_from_map(series_map)
            )

def _instance_sort_key(instance: DicomInstanceMeta) -> tuple[int, str]:
    instance_number = (
        instance.instance_number if instance.instance_number is not None else 1_000_000
    )
    return instance_number, str(instance.path)


def _series_sort_key(series: DicomSeriesSummary) -> tuple[str, str, int, str, str]:
    series_number = series.series_number if series.series_number is not None else 1_000_000
    return (
        series.patient_name,
        series.study_description,
        series_number,
        series.series_description,
        series.series_instance_uid,
    )