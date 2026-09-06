"""Classic PET 2D capability checks."""

from qt_dicom_viewer.model import DicomSeriesRecord


PET_IMAGE_STORAGE_UID = "1.2.840.10008.5.1.4.1.1.128"
ENHANCED_PET_IMAGE_STORAGE_UID = "1.2.840.10008.5.1.4.1.1.130"
LEGACY_CONVERTED_ENHANCED_PET_IMAGE_STORAGE_UID = (
    "1.2.840.10008.5.1.4.1.1.128.1"
)


class UnsupportedPetSeriesError(ValueError):
    pass


def pet_2d_support_error(
    *,
    modality: str,
    sop_class_uid: str,
    number_of_frames: int,
    photometric_interpretation: str,
    series_type: tuple[str, ...],
) -> str:
    """Return an empty string when one instance is eligible for PET 2D v1."""
    if modality.upper() != "PT":
        return ""
    if sop_class_uid in {
        ENHANCED_PET_IMAGE_STORAGE_UID,
        LEGACY_CONVERTED_ENHANCED_PET_IMAGE_STORAGE_UID,
    }:
        return "PET 2D 第一版暂不支持 Enhanced PET 多帧影像"
    if sop_class_uid != PET_IMAGE_STORAGE_UID:
        return "PET 2D 第一版仅支持经典 PET Image Storage"
    if number_of_frames != 1:
        return "PET 2D 第一版暂不支持多帧 PET 影像"
    if photometric_interpretation.upper() != "MONOCHROME2":
        return "经典 PET 2D 仅支持 MONOCHROME2 灰阶影像"

    normalized_type = tuple(value.upper() for value in series_type)
    if len(normalized_type) < 2:
        return "PET Series Type 缺失，无法确认空间与时间维度"
    if normalized_type[0] not in {"STATIC", "WHOLE BODY"}:
        return f"PET 2D 第一版暂不支持 {normalized_type[0]} 序列"
    if normalized_type[1] != "IMAGE":
        return "PET 2D 第一版暂不支持 REPROJECTION 影像"
    return ""


def validate_pet_2d_series(series: DicomSeriesRecord) -> None:
    """Reject PET encodings whose dimensions cannot be represented by 2D v1."""
    if series.modality.upper() != "PT":
        return

    for instance in series.instances:
        error = pet_2d_support_error(
            modality=instance.modality,
            sop_class_uid=instance.sop_class_uid,
            number_of_frames=instance.number_of_frames,
            photometric_interpretation=(
                instance.photometric_interpretation
            ),
            series_type=instance.pet_series_type,
        )
        if error:
            raise UnsupportedPetSeriesError(error)

    series_types = {
        tuple(value.upper() for value in instance.pet_series_type)
        for instance in series.instances
    }
    if len(series_types) != 1:
        raise UnsupportedPetSeriesError(
            "PET Series Type 在同一序列中不一致"
        )
