from qt_dicom_viewer.model import DicomFolderScanSnapshot, DicomSeriesRecord, SeriesDisplayMeta


class SeriesCatalog:
    def __init__(self) -> None:
        self._series_by_uid: dict[str, DicomSeriesRecord] = {}

    def update(self, process: DicomFolderScanSnapshot) -> None:
        for series in process.series:
            self._series_by_uid[series.series_instance_uid] = series

    def snapshot(self):
        """Copy the index for background import; records are replaced, not mutated."""
        return dict(self._series_by_uid)

    def get_series(self, series_uid: str) -> DicomSeriesRecord | None:
        return self._series_by_uid.get(series_uid)

    def get_series_display_meta(self, series_uid: str) -> SeriesDisplayMeta | None:
        series = self._series_by_uid.get(series_uid, None)
        if series is None:
            return None
        first_instance = series.instances[0] if series.instances else None
        return SeriesDisplayMeta(
            series_uid=series.series_instance_uid,
            patient_name=series.patient_name,
            patient_id=series.patient_id,
            modality=series.modality,
            study_description=series.study_description,
            series_description=series.series_description,
            phase_identifiers=series.phase_identifiers,
            supports_four_d=series.supports_four_d,
            initial_phase_identifier=series.initial_phase_identifier,
            slice_count=series.dicom_file_count,
            rows=series.rows,
            columns=series.columns,
            series_number=series.series_number,
            pixel_spacing=(
                first_instance.pixel_spacing
                if first_instance else None
            ),
            patient_sex=(
                first_instance.patient_sex if first_instance else ""
            ),
            patient_age=(
                first_instance.patient_age if first_instance else ""
            ),
            acquisition_datetime=(
                first_instance.acquisition_datetime
                if first_instance else ""
            ),
            kvp=first_instance.kvp if first_instance else None,
            tube_current_ma=(
                first_instance.tube_current_ma
                if first_instance else None
            ),
            slice_thickness=(
                first_instance.slice_thickness
                if first_instance else None
            ),
        )
