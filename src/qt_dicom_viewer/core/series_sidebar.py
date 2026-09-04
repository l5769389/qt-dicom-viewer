"""Patient / study / series rows for the virtualized sidebar."""

from hashlib import sha1

from qt_dicom_viewer.model import DicomSeriesRecord


def patient_key(series: DicomSeriesRecord) -> str:
    # Names are not unique identifiers. With no patient ID, keep studies separate.
    identity = (series.patient_id, series.patient_id_issuer) if series.patient_id else (
        "study", series.study_instance_uid or series.series_instance_uid)
    return "patient-" + sha1(repr(identity).encode()).hexdigest()


def study_label(series: DicomSeriesRecord) -> str:
    date, time = series.study_date, series.study_time.split(".")[0]
    label = f"{date[:4]}/{date[4:6]}/{date[6:8]}" if len(date) == 8 and date.isdigit() else "日期未知"
    if len(time) >= 4 and time.isdigit():
        label += f" {time[:2]}:{time[2:4]}" + (f":{time[4:6]}" if len(time) >= 6 else "")
    return label


def build_sidebar_rows(records, query: str, collapsed: set[str], thumbnails: dict[str, str]):
    patients = {}
    for series in records:
        key = patient_key(series)
        patient = patients.setdefault(key, {"series": series, "studies": {}})
        study_uid = series.study_instance_uid or series.series_instance_uid
        patient["studies"].setdefault(study_uid, []).append(series)
    query = query.strip().casefold()
    rows = []

    def row(kind, key, label, **kwargs):
        return dict(kind=kind, key=key, label=label, subtitle="", seriesInstanceUid="",
                    modality="", thumbnailUrl="", dicomFileCount=0, expanded=True, **kwargs)

    for key, patient in sorted(patients.items(), key=lambda entry: (
        entry[1]["series"].patient_name.casefold(), entry[1]["series"].patient_id, entry[0])):
        first = patient["series"]
        if query and not any(query in f"{s.patient_name} {s.patient_id}".casefold()
                             for study in patient["studies"].values() for s in study):
            continue
        expanded = bool(query) or key not in collapsed
        item = row("patient", key, first.patient_name or "未知患者")
        item.update(subtitle=first.patient_id, expanded=expanded)
        rows.append(item)
        if not expanded:
            continue
        for study_uid, series_list in sorted(patient["studies"].items(), key=lambda entry: (
            entry[1][0].study_date, entry[1][0].study_time, entry[0]), reverse=True):
            first_series = series_list[0]
            study_key = key + "/study-" + study_uid
            expanded = bool(query) or study_key not in collapsed
            item = row("study", study_key, study_label(first_series))
            item.update(subtitle=first_series.study_description, expanded=expanded)
            rows.append(item)
            if not expanded:
                continue
            for series in sorted(series_list, key=lambda s: (
                s.series_number if s.series_number is not None else 1_000_000, s.series_instance_uid)):
                item = row("series", series.series_instance_uid, series.series_description or "[无描述]")
                item.update(
                    seriesInstanceUid=series.series_instance_uid,
                    modality=series.modality,
                    subtitle=" · ".join(filter(None, [series.modality,
                        f"Series {series.series_number}" if series.series_number is not None else ""])),
                    thumbnailUrl=thumbnails.get(series.series_instance_uid, ""),
                    dicomFileCount=series.dicom_file_count,
                )
                rows.append(item)
    return rows
