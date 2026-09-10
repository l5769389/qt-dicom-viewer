"""在 Windows 上生成包含 Python、Qt 和 QML 资源的单文件 EXE。"""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path

from packaging_utils import prepare_assets

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def pyinstaller_command(root: Path, *, console: bool = False, installer: bool = False,
                        icon: Path | None = None) -> list[str]:
    """集中声明打包参数，资源位置不依赖调用者的工作目录。"""
    root = root.resolve()
    qml_directory = root / "src" / "qt_dicom_viewer" / "qml"
    entry = root / "scripts" / "windows_entry.py"
    if not (qml_directory / "Main.qml").is_file() or not entry.is_file():
        raise FileNotFoundError("找不到应用入口或 QML 资源，请使用完整项目目录打包。")

    name = "Voxenra-debug" if console else "Voxenra"
    return [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir" if installer else "--onefile",
        "--console" if console else "--windowed",
        # 不使用 UPX 压缩 Qt DLL，避免插件损坏和额外的工具依赖。
        "--noupx",
        "--name", name,
        "--icon", str(icon or root / "build/installer-assets/app.ico"),
        "--distpath", str(root / "dist" / "windows" if installer else root / "dist"),
        "--workpath", str(root / "build" / "windows" / name),
        "--specpath", str(root / "build" / "windows"),
        "--paths", str(root / "src"),
        "--additional-hooks-dir", str(root / "packaging" / "hooks"),
        # hook-qt_dicom_viewer.py preserves package-relative QML/SVG/brand assets
        # and omits superseded PNG icon originals (still kept in the repository).
        "--add-data", f"{root / 'licenses'}:licenses",
        # 这些模块也会由 QML 间接使用，显式触发 Qt 的插件收集钩子。
        "--hidden-import", "PySide6.QtQuick",
        "--hidden-import", "PySide6.QtQuickControls2",
        "--hidden-import", "PySide6.QtSvg",
        # Python VTK uses factories and a dynamically selected Qt binding.
        "--hidden-import", "vtkmodules.qt.QVTKRenderWindowInteractor",
        "--hidden-import", "vtkmodules.vtkRenderingOpenGL2",
        "--hidden-import", "vtkmodules.vtkRenderingVolumeOpenGL2",
        "--hidden-import", "vtkmodules.vtkRenderingFreeType",
        "--hidden-import", "vtkmodules.vtkInteractionStyle",
        # Archive readers include native libraries; no external unrar executable.
        "--collect-all", "py7zr",
        "--collect-all", "unrar",
        "--hidden-import", "_cffi_backend",
        "--copy-metadata", "unrar2-cffi",
        # pydicom 动态解码模块和数据文件由其官方打包钩子收集。
        str(entry),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--console", action="store_true",
        help="生成带控制台的 Voxenra-debug.exe，便于排查启动和 QML 错误。",
    )
    args = parser.parse_args(argv)

    if sys.platform != "win32":
        print("请在 Windows 上运行此脚本；PyInstaller 不支持跨平台生成 Windows EXE。", file=sys.stderr)
        return 1
    if platform.machine().lower() not in {"amd64", "x86_64"} or sys.maxsize <= 2**32:
        print("此打包入口要求 Windows x64 和 64 位 Python。", file=sys.stderr)
        return 1
    if sys.version_info[:2] != (3, 13):
        print("请使用 scripts\\build_windows.bat，以 Python 3.13 和锁定依赖打包。", file=sys.stderr)
        return 1

    try:
        prepare_assets(PROJECT_ROOT)
        command = pyinstaller_command(PROJECT_ROOT, console=args.console)
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"打包失败：{error}", file=sys.stderr)
        return error.returncode if isinstance(error, subprocess.CalledProcessError) else 1

    name = "Voxenra-debug" if args.console else "Voxenra"
    executable = PROJECT_ROOT / "dist" / f"{name}.exe"
    if not executable.is_file():
        print(f"打包没有生成预期文件：{executable}", file=sys.stderr)
        return 1
    print(f"打包完成：{executable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
