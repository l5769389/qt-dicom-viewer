"""Transactional series export. Source files are always read-only."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import shutil
import tempfile
from threading import Event
import uuid

import pydicom
from pydicom.pixels import iter_pixels

from qt_dicom_viewer.core.dicom_anonymizer import Anonymizer, check_pixel_identity
from qt_dicom_viewer.core.export_images import frame_image


class ExportCancelled(Exception):
    pass


class ExportError(ValueError):
    """User-facing errors must not include source paths or patient metadata."""


@dataclass(frozen=True)
class ExportRequest:
    paths: tuple[Path, ...]
    directory: Path
    format: str = "dicom"
    anonymous: bool = True


@dataclass(frozen=True)
class ExportResult:
    directory: Path
    file_count: int


def export_series(request: ExportRequest, *, cancel=None, progress=None):
    cancel = cancel or Event()
    progress = progress or (lambda completed, total: None)

    def check_cancelled():
        if cancel.is_set():
            raise ExportCancelled()

    if request.format not in ("png", "dicom"):
        raise ExportError("请选择 PNG 或 DICOM 格式")
    paths = tuple(dict.fromkeys(Path(path) for path in request.paths))
    if not paths:
        raise ExportError("所选序列没有可导出的文件")
    root = Path(request.directory).expanduser()
    if not root.is_absolute():
        raise ExportError("导出位置必须是绝对目录路径")
    stage = None
    try:
        # Validate all inputs before publishing any output, including late-series
        # burned-in annotations and multi-frame image counts.
        frame_counts = []
        for index, path in enumerate(paths, 1):
            check_cancelled()
            try:
                header = pydicom.dcmread(path, stop_before_pixels=True)
                if request.anonymous:
                    check_pixel_identity(header)
                frame_counts.append(max(1, int(getattr(header, "NumberOfFrames", 1))))
            except ValueError as exc:
                if str(exc).startswith("匿名导出"):
                    raise ExportError(str(exc)) from exc
                raise ExportError(f"无法读取第 {index} 个 DICOM 文件，请检查源文件") from exc
            except Exception as exc:
                raise ExportError(f"无法读取第 {index} 个 DICOM 文件，请检查源文件") from exc
        total = sum(frame_counts) if request.format == "png" else len(paths)
        progress(0, total)
        root.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=".export-", dir=root))
        anonymizer = Anonymizer()
        completed = 0
        for index, path in enumerate(paths, 1):
            check_cancelled()
            try:
                if request.format == "dicom":
                    output = stage / f"instance-{index:06d}.dcm"
                    if request.anonymous:
                        dataset = pydicom.dcmread(path)
                        anonymizer.apply(dataset)
                        dataset.save_as(output, enforce_file_format=True)
                    else:
                        shutil.copyfile(path, output)
                    completed += 1
                    progress(completed, total)
                else:
                    dataset = pydicom.dcmread(path, stop_before_pixels=True)
                    count = 0
                    for frame_index, pixels in enumerate(iter_pixels(path)):
                        check_cancelled()
                        image = frame_image(pixels, dataset, frame_index)
                        if not request.anonymous:
                            for key in ("PatientName", "PatientID", "StudyInstanceUID", "SeriesInstanceUID"):
                                image.setText(key, str(getattr(dataset, key, "")))
                        output = stage / f"instance-{index:06d}-frame-{frame_index + 1:06d}.png"
                        if not image.save(str(output), "PNG"):
                            raise ExportError("PNG 写入失败，请检查导出目录空间和权限")
                        completed += 1
                        count += 1
                        progress(completed, total)
                    if count != frame_counts[index - 1]:
                        raise ExportError(f"第 {index} 个文件的帧数不一致，导出已取消")
            except (ExportCancelled, ExportError):
                raise
            except Exception as exc:
                raise ExportError(f"第 {index} 个文件导出失败，请检查文件完整性、图像解码支持及目录权限") from exc
        check_cancelled()
        name = "series-" + datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:12]
        destination = root / name
        stage.rename(destination)
        stage = None
        return ExportResult(destination, completed)
    except (ExportCancelled, ExportError):
        raise
    except OSError as exc:
        raise ExportError("无法写入导出目录，请检查目录权限和剩余空间") from exc
    finally:
        if stage is not None:
            shutil.rmtree(stage)
