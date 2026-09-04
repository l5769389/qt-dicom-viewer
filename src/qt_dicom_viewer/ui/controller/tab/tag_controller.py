"""Per-tab instance navigation and metadata presentation state."""

import re
from uuid import uuid4

from PySide6.QtCore import QObject, Property, Signal, Slot

from qt_dicom_viewer.model import DicomSeriesRecord
from qt_dicom_viewer.model.dicom_tags import TagReadRequest, TagReadResult
from qt_dicom_viewer.service.tag_read_service import TagReadService
from qt_dicom_viewer.ui.controller.tab.tag_tree_model import TagTreeModel


class TagController(QObject):
    stateChanged = Signal()
    queryChanged = Signal()
    viewStateChanged = Signal()
    instanceChanged = Signal()

    def __init__(self, tab_id: str, series: DicomSeriesRecord, service: TagReadService, parent=None):
        super().__init__(parent)
        self._tab_id = tab_id
        self._series = series
        self._service = service
        self._model = TagTreeModel(self)
        self._page = 1 if series.instances else 0
        self._query = ""
        self._loading = False
        self._error = self._page_error = ""
        self._request: TagReadRequest | None = None
        self._closed = False
        self._scroll = 0.0
        self._selected = ""
        service.finished.connect(self._accept_result)

    @Property(QObject, constant=True)
    def tagModel(self):
        return self._model

    @Property(str, constant=True)
    def modality(self):
        return self._series.modality or "DICOM"

    @Property(int, constant=True)
    def pageCount(self):
        return len(self._series.instances)

    @Property(int, notify=stateChanged)
    def currentPage(self):
        return self._page

    @Property(str, notify=stateChanged)
    def sopInstanceUid(self):
        return self._series.instances[self._page - 1].sop_instance_uid if self._page else ""

    @Property(str, notify=stateChanged)
    def filePath(self):
        return str(self._series.instances[self._page - 1].path) if self._page else ""

    @Property(str, notify=queryChanged)
    def searchText(self):
        return self._query

    @Property(bool, notify=stateChanged)
    def loading(self):
        return self._loading

    @Property(str, notify=stateChanged)
    def errorMessage(self):
        return self._error

    @Property(str, notify=stateChanged)
    def pageError(self):
        return self._page_error

    @Property(float, notify=viewStateChanged)
    def scrollPosition(self):
        return self._scroll

    @Property(str, notify=viewStateChanged)
    def selectedNodeId(self):
        return self._selected

    @Property("QVariantList", notify=stateChanged)
    def pageItems(self):
        if not self.pageCount:
            return []
        start = max(1, min(self._page - 2, self.pageCount - 4))
        pages = sorted({1, self.pageCount, *range(start, min(start + 5, self.pageCount + 1))})
        result = []
        previous = 0
        for page in pages:
            if previous and page - previous > 1:
                result.append(0)
            result.append(page)
            previous = page
        return result

    @Slot(int)
    def setPage(self, page: int) -> None:
        if self._closed:
            return
        if not 1 <= page <= self.pageCount:
            self._page_error = f"请输入 1–{self.pageCount} 的页码" if self.pageCount else "没有可浏览的实例"
            self.stateChanged.emit()
            return
        self._page_error = ""
        if page == self._page:
            self.stateChanged.emit()
            return
        self._page = page
        self._load()

    @Slot(str)
    def jumpToPage(self, value: str) -> None:
        value = value.strip()
        self.setPage(int(value) if re.fullmatch(r"[0-9]{1,9}", value) else -1)

    @Slot(str)
    def setSearchText(self, query: str) -> None:
        if query == self._query:
            return
        self._query = query
        self._model.set_query(query)
        self._scroll = 0.0
        self._selected = ""
        self.queryChanged.emit()
        self.viewStateChanged.emit()

    @Slot(str)
    def toggleNode(self, node_id: str) -> None:
        self._model.toggle(node_id)

    @Slot(float)
    def saveScrollPosition(self, position: float) -> None:
        # The view already has this position. Avoid a binding feedback loop while flicking.
        self._scroll = max(0.0, position)

    @Slot(str)
    def selectNode(self, node_id: str) -> None:
        self._selected = node_id
        self.viewStateChanged.emit()

    @Slot()
    def retry(self) -> None:
        if not self._loading:
            self._load()

    def start(self) -> None:
        self._load()

    def _load(self) -> None:
        if self._closed or not self._page:
            return
        self._loading = True
        self._error = self._page_error = ""
        self._scroll = 0.0
        self._selected = ""
        self._model.set_nodes(())
        instance = self._series.instances[self._page - 1]
        self._request = TagReadRequest(str(uuid4()), self._tab_id, instance.sop_instance_uid, instance.path)
        self.stateChanged.emit()
        self.viewStateChanged.emit()
        self.instanceChanged.emit()
        self._service.submit(self._request)

    @Slot(object)
    def _accept_result(self, result: TagReadResult) -> None:
        if self._closed or result.request != self._request:
            return
        self._loading = False
        self._error = result.error
        self._model.set_nodes(result.nodes if not result.error else ())
        self.stateChanged.emit()

    def dispose(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._service.cancel(self._tab_id)
        self._service.finished.disconnect(self._accept_result)
