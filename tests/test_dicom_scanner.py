from pathlib import Path

from qt_dicom_viewer.core.dicom_scanner import _iter_visible_files

#
# a.txt
# b.txt
# .hidden.txt
# visible
#    /nested.txt
# .hidden-dir
#    /should-not-appear.txt
def create_path(tmp_path: Path) -> None:
    (tmp_path / "b.txt").touch()
    (tmp_path / "a.txt").touch()
    (tmp_path / ".hidden.txt").touch()

    visible_dir = tmp_path / "visible"
    visible_dir.mkdir()
    (visible_dir / "nested.txt").touch()

    hidden_dir = tmp_path / ".hidden-dir"
    hidden_dir.mkdir()
    (hidden_dir / "should-not-appear.txt").touch()

def test_iter_visible_files_skips_hidden_entries_and_recurses(tmp_path: Path) -> None:
    create_path(tmp_path)


def test_iter_visible_files(tmp_path:Path) -> None:
    create_path(tmp_path)
    _iter_visible_files(tmp_path)
