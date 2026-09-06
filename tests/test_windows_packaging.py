"""验证打包参数、平台保护和无控制台日志；不替代 Windows 真机验收。"""

from __future__ import annotations

import importlib.util
import io
import logging
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from qt_dicom_viewer.infrastructure import logging_config

PROJECT_ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "build_windows", PROJECT_ROOT / "scripts" / "build_windows.py"
)
build_windows = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_windows)


def test_onefile_build_keeps_package_resource_layout() -> None:
    command = build_windows.pyinstaller_command(PROJECT_ROOT)

    assert "--onefile" in command
    assert "--windowed" in command
    assert "--console" not in command
    assert command[command.index("--name") + 1] == "DICOMVision"
    assert command[command.index("--add-data") + 1] == (
        f"{PROJECT_ROOT / 'src/qt_dicom_viewer/qml'}:qt_dicom_viewer/qml"
    )
    assert command[-1] == str(PROJECT_ROOT / "scripts/windows_entry.py")
    assert {"PySide6.QtQuick", "PySide6.QtQuickControls2", "PySide6.QtSvg"} <= set(command)
    assert {
        "vtkmodules.qt.QVTKRenderWindowInteractor", "vtkmodules.vtkRenderingOpenGL2",
        "vtkmodules.vtkRenderingVolumeOpenGL2", "vtkmodules.vtkRenderingFreeType",
        "vtkmodules.vtkInteractionStyle",
    } <= set(command)
    assert (
        PROJECT_ROOT
        / "src/qt_dicom_viewer/qml/sections/center/viewportArea/MontageViewport.qml"
    ).is_file()


def test_console_build_uses_separate_executable() -> None:
    command = build_windows.pyinstaller_command(PROJECT_ROOT, console=True)

    assert "--console" in command
    assert "--windowed" not in command
    assert command[command.index("--name") + 1] == "DICOMVision-debug"


def test_build_paths_do_not_depend_on_working_directory(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    command = build_windows.pyinstaller_command(PROJECT_ROOT)

    assert command[command.index("--distpath") + 1] == str(PROJECT_ROOT / "dist")
    assert command[command.index("--paths") + 1] == str(PROJECT_ROOT / "src")


def test_incomplete_source_tree_is_rejected(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="QML"):
        build_windows.pyinstaller_command(tmp_path)


def test_non_windows_host_does_not_start_packager(monkeypatch, capsys) -> None:
    monkeypatch.setattr(build_windows.sys, "platform", "darwin")
    monkeypatch.setattr(
        build_windows.subprocess, "run",
        lambda *args, **kwargs: pytest.fail("非 Windows 环境不应执行打包"),
    )

    assert build_windows.main([]) == 1
    assert "Windows" in capsys.readouterr().err


@pytest.fixture
def simulated_windows(monkeypatch):
    monkeypatch.setattr(build_windows.sys, "platform", "win32")
    monkeypatch.setattr(build_windows.sys, "version_info", (3, 13, 0))
    monkeypatch.setattr(build_windows.sys, "maxsize", 2**63 - 1)
    monkeypatch.setattr(build_windows.platform, "machine", lambda: "AMD64")


def test_build_failure_preserves_nonzero_exit_code(simulated_windows, monkeypatch) -> None:
    def failed_build(command, **kwargs):
        assert kwargs["check"] is True
        raise subprocess.CalledProcessError(2, command)

    monkeypatch.setattr(build_windows.subprocess, "run", failed_build)

    assert build_windows.main([]) == 2


def test_success_without_output_is_reported_as_failure(
    simulated_windows, monkeypatch, tmp_path,
) -> None:
    monkeypatch.setattr(build_windows, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(build_windows, "pyinstaller_command", lambda *a, **kw: ["packager"])
    monkeypatch.setattr(build_windows.subprocess, "run", lambda *a, **kw: None)

    assert build_windows.main([]) == 1


def test_success_requires_expected_executable(simulated_windows, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(build_windows, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(build_windows, "pyinstaller_command", lambda *a, **kw: ["packager"])

    def successful_build(*args, **kwargs):
        (tmp_path / "dist").mkdir()
        (tmp_path / "dist" / "DICOMVision.exe").touch()

    monkeypatch.setattr(build_windows.subprocess, "run", successful_build)

    assert build_windows.main([]) == 0


@pytest.mark.parametrize("has_console", [False, True])
def test_logging_works_with_and_without_console(has_console, monkeypatch, tmp_path) -> None:
    console = io.StringIO() if has_console else None
    monkeypatch.setattr(logging_config.sys, "stdout", console)
    monkeypatch.setattr(logging_config.sys, "stderr", console)
    monkeypatch.setattr(logging_config, "QStandardPaths", SimpleNamespace(
        AppLocalDataLocation=0,
        writableLocation=lambda _: str(tmp_path),
    ))
    configuration = {}
    # 不修改 pytest 的根日志配置，只捕获待安装的处理器进行验证。
    monkeypatch.setattr(logging_config.logging, "basicConfig", lambda **kw: configuration.update(kw))

    log_path = logging_config.configure_logging()
    logger = logging.Logger("packaged-app")
    logger.handlers = configuration["handlers"]
    try:
        logger.warning("文件日志正常")
        assert "文件日志正常" in log_path.read_text(encoding="utf-8")
        assert len(logger.handlers) == (2 if has_console else 1)
        if has_console:
            assert "文件日志正常" in console.getvalue()
    finally:
        for handler in logger.handlers:
            handler.close()
