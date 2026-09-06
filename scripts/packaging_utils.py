"""安装包元数据、资源格式转换；不读取或打包用户影像。"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "DICOMVision"
BUNDLE_ID = "com.junliu.dicomvision"


def app_version(root: Path = PROJECT_ROOT) -> str:
    with (root / "pyproject.toml").open("rb") as stream:
        version = tomllib.load(stream)["project"]["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("安装包版本必须使用 major.minor.patch 数字格式。")
    return version


def prepare_assets(root: Path = PROJECT_ROOT) -> Path:
    """复用现有品牌图片，只导出操作系统所需的 ICO / ICNS 格式。"""
    from PIL import Image

    output = root / "build" / "installer-assets"
    output.mkdir(parents=True, exist_ok=True)
    with Image.open(root / "src/qt_dicom_viewer/qml/assets/brand/dicomvision-mark.png") as source:
        icon = source.convert("RGBA")
        icon.save(output / "app.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
        icon.save(output / "app.icns")
        icon.resize((256, 256)).save(output / "wizard-logo.png")
    return output
