"""One mixed file/directory picker; Qt's native file modes cannot express both."""

from pathlib import Path

from PySide6.QtCore import QEvent, QDir, QItemSelectionModel, QStandardPaths, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFileSystemModel,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeView,
    QVBoxLayout,
)


class ImportFileModel(QFileSystemModel):
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and 0 <= section < 4:
            return ("名称", "大小", "类型", "修改时间")[section]
        return super().headerData(section, orientation, role)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and index.column() == 2 and self.isDir(index):
            return "文件夹"
        return super().data(index, role)


class LocalImportDialog(QDialog):
    def __init__(self, directory="", parent=None):
        super().__init__(parent)
        self.setObjectName("localImportDialog")
        self.setWindowTitle("打开影像")
        self.resize(880, 560)
        self.setMinimumSize(620, 400)
        self.paths = []
        self._directory = ""
        self.setStyleSheet("""
            QDialog { background: #171c22; color: #edf1f5; }
            QLabel { color: #c3ccd5; }
            QLineEdit, QTreeView { background: #101317; color: #edf1f5;
                border: 1px solid #36414d; border-radius: 4px; padding: 5px; }
            QTreeView::item { height: 28px; }
            QTreeView::item:selected { background: #203b4c; color: #edf1f5; }
            QHeaderView::section { background: #202831; color: #c3ccd5;
                padding: 6px; border: none; }
            QPushButton { background: #202831; color: #edf1f5; padding: 7px 12px;
                border: 1px solid #36414d; border-radius: 4px; }
            QPushButton:hover { background: #2b3743; }
            QPushButton:disabled { color: #73808c; }
            QPushButton#importOpen { background: #21698f; color: #f8fafc; border-color: #579fc6; }
            QPushButton#importOpen:hover { background: #2b82ad; }
            QPushButton#importOpen:pressed { background: #195574; }
            QPushButton#importOpen:disabled { background: #183344; color: #73808c; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        # The native dialog caption owns the only close control on every platform.
        heading = QLabel("选择影像来源")
        heading.setStyleSheet("font-size: 16px; font-weight: 600; color: #edf1f5;")
        layout.addWidget(heading)
        location = QHBoxLayout()
        for title, navigate in (
            ("上一级", self.up),
            ("主目录", lambda: self.navigate(str(Path.home()))),
            ("计算机", lambda: self.navigate("")),
        ):
            button = QPushButton(title)
            button.setAutoDefault(False)
            button.clicked.connect(navigate)
            location.addWidget(button)
        self.path_edit = QLineEdit()
        self.path_edit.setObjectName("importPath")
        self.path_edit.setPlaceholderText("文件夹或文件路径")
        self.path_edit.installEventFilter(self)
        location.addWidget(self.path_edit, 1)
        layout.addLayout(location)
        hint = QLabel(
            "可同时选择文件夹、文件和压缩包；按住 Ctrl / ⌘ 多选，双击文件夹进入。"
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.model = ImportFileModel(self)
        self.model.setReadOnly(True)
        self.model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self.view = QTreeView()
        self.view.setObjectName("importFileList")
        self.view.setModel(self.model)
        self.view.setRootIsDecorated(False)
        self.view.setItemsExpandable(False)
        self.view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.view.setSortingEnabled(True)
        self.view.sortByColumn(0, Qt.AscendingOrder)
        self.view.setColumnWidth(0, 420)
        self.view.doubleClicked.connect(self.open_item)
        self.view.selectionModel().selectionChanged.connect(self.update_selection)
        layout.addWidget(self.view, 1)
        self.selection_label = QLabel()
        self.selection_label.setObjectName("importSelectionSummary")
        layout.addWidget(self.selection_label)
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addStretch(1)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("importCancel")
        self.cancel_button.setAutoDefault(False)
        self.cancel_button.setMinimumWidth(80)
        self.cancel_button.clicked.connect(self.reject)
        buttons.addWidget(self.cancel_button)
        self.open_button = QPushButton()
        self.open_button.setObjectName("importOpen")
        self.open_button.setMinimumWidth(144)
        self.open_button.setDefault(True)
        self.open_button.clicked.connect(self.accept)
        buttons.addWidget(self.open_button)
        layout.addLayout(buttons)
        initial = (
            directory
            or QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
            or str(Path.home())
        )
        self.navigate(initial if Path(initial).is_dir() else str(Path.home()))

    def eventFilter(self, watched, event):
        if (
            watched is self.path_edit
            and event.type() == QEvent.KeyPress
            and event.key() in (Qt.Key_Return, Qt.Key_Enter)
        ):
            self.open_typed_path()
            return True
        return super().eventFilter(watched, event)

    def selected_paths(self):
        return [
            self.model.filePath(index)
            for index in self.view.selectionModel().selectedRows(0)
        ]

    def navigate(self, directory):
        if directory and not Path(directory).is_dir():
            return
        self._directory = str(Path(directory).resolve()) if directory else ""
        self.model.setRootPath(self._directory)
        self.view.setRootIndex(self.model.index(self._directory))
        self.view.clearSelection()
        self.path_edit.setText(self._directory)
        self.update_selection()

    def up(self):
        if self._directory:
            parent = str(Path(self._directory).parent)
            self.navigate("" if parent == self._directory else parent)

    def open_typed_path(self):
        path = Path(self.path_edit.text()).expanduser()
        if path.is_dir():
            self.navigate(str(path))
        elif path.is_file():
            self.navigate(str(path.parent))
            index = self.model.index(str(path.resolve()))
            self.view.selectionModel().select(
                index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows
            )
            self.view.scrollTo(index)
        else:
            self.selection_label.setText("路径不存在，请检查后重新输入。")

    def open_item(self, index):
        if self.model.isDir(index):
            self.navigate(self.model.filePath(index))
        else:
            self.accept()

    def update_selection(self, *_):
        paths = self.selected_paths()
        directories = sum(Path(path).is_dir() for path in paths)
        self.selection_label.setText(
            f"已选择 {directories} 个文件夹、{len(paths) - directories} 个文件"
            if paths
            else "未选择项目时，可直接打开当前文件夹。"
        )
        self.open_button.setText("打开所选" if paths else "打开当前文件夹")
        self.open_button.setEnabled(bool(paths or self._directory))

    def accept(self):
        paths = self.selected_paths() or ([self._directory] if self._directory else [])
        if not paths or not all(Path(path).exists() for path in paths):
            self.selection_label.setText("所选项目已移动或不存在，请重新选择。")
            return
        self.paths = paths
        super().accept()


def select_import_paths(directory=""):
    owner = QGuiApplication.focusWindow()
    dialog = LocalImportDialog(directory)
    if owner is not None:
        dialog.winId()
        dialog.windowHandle().setTransientParent(owner)
    try:
        return dialog.paths if dialog.exec() == QDialog.Accepted else []
    finally:
        dialog.deleteLater()
