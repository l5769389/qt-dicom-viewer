from qt_dicom_viewer.core.dicom_models import DicomSeriesSummary, DicomFolderScanSnapshot, SeriesDisplayMeta


class SeriesCatalog:
    def __init__(self) -> None:
        self._series_by_uid: dict[str, DicomSeriesSummary] = {}

    def update(self, process: DicomFolderScanSnapshot) -> None:
        for series in process.series:
            self._series_by_uid[series.series_instance_uid] = series

    def get_series(self, series_uid: str) -> DicomSeriesSummary | None:
        return self._series_by_uid.get(series_uid)

    def get_series_display_meta(self, series_uid: str) -> SeriesDisplayMeta | None:
        series = self._series_by_uid.get(series_uid, None)
        if series is None:
            return None
        return SeriesDisplayMeta(
            series_uid=series.series_instance_uid,
            patient_name=series.patient_name,
            patient_id=series.patient_id,
            modality=series.modality,
            study_description=series.study_description,
            series_description=series.series_description,
        )