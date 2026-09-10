"""Collect Voxenra's Qt Quick runtime without unrelated browser/3D QML engines.

Filter before PyInstaller analyzes binary dependencies; deleting libraries after
freezing could leave plugins with missing dependencies. Keep all Controls styles
and their Qt/labs support so native Windows/macOS style selection still works.
"""
from pathlib import PurePosixPath

from PyInstaller.utils.hooks.qt import add_qt6_dependencies, pyside6_library_info


def used_qml_module(destination):
    parts = PurePosixPath(str(destination).replace("\\", "/")).parts
    if "qml" not in parts:
        raise ValueError(f"Unexpected Qt QML destination: {destination}")
    module = parts[parts.index("qml") + 1:]
    if not module:
        return True
    if module[0] not in {"QtQml", "QtQuick", "QtCore", "Qt", "Qt5Compat"}:
        return False
    # Optional bridges, PDF views and the touch keyboard are not used by Voxenra.
    return module[:2] not in {
        ("QtQuick", "Scene2D"), ("QtQuick", "Scene3D"),
        ("QtQuick", "Pdf"), ("QtQuick", "VirtualKeyboard"),
    }


hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
qml_binaries, qml_datas = pyside6_library_info.collect_qtqml_files()
binaries += [entry for entry in qml_binaries if used_qml_module(entry[1])]
datas += [entry for entry in qml_datas if used_qml_module(entry[1])]
