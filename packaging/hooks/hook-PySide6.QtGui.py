"""Keep desktop image/input plugins; omit PDF and the QML touch keyboard."""
from pathlib import Path
from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
binaries = [entry for entry in binaries
            if Path(entry[0]).stem.removeprefix("lib") not in {"qpdf", "qtvirtualkeyboardplugin"}]
