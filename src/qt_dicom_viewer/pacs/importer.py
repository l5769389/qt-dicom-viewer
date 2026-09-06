from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from qt_dicom_viewer.core.dicom_scanner import DicomFolderScanner
from qt_dicom_viewer.model import DicomFolderScanSnapshot
from .client import DicomWebClient, PacsError, check_cancel


@dataclass
class PacsImportResult:
    folder: Path
    snapshot: DicomFolderScanSnapshot

    def discard(self):
        shutil.rmtree(self.folder, ignore_errors=True)


def import_series(client: DicomWebClient, selections: list[dict], root: Path, progress) -> PacsImportResult:
    root.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="import-", dir=root))
    try:
        requests = []
        for series in selections:
            check_cancel(client.cancel)
            progress(0, "正在查询序列实例…")
            instances = client.instance_uids(series["studyUid"], series["uid"])
            expected = str(series.get("instances", ""))
            if expected.isdigit() and int(expected) != len(instances):
                raise PacsError("PACS 实例数量与序列信息不一致，请重新查询后重试。")
            requests.extend((series["studyUid"], series["uid"], sop) for sop in instances)
        for index, (study, series, sop) in enumerate(requests):
            client.download_instance(study, series, sop, folder / f"{index:06d}.dcm")
            progress((index + 1) / len(requests), f"已下载 {index + 1} / {len(requests)} 个实例")
        snapshot = None
        for snapshot in DicomFolderScanner().scan(folder):
            check_cancel(client.cancel)
        if snapshot is None or snapshot.dicom_file_count != len(requests) or snapshot.skipped_file_count:
            raise PacsError("下载文件未能全部载入，导入已取消。")
        check_cancel(client.cancel)
        return PacsImportResult(folder, snapshot)
    except BaseException:
        shutil.rmtree(folder, ignore_errors=True)
        raise
