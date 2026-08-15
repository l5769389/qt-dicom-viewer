import logging
from dataclasses import dataclass

from PySide6.QtCore import (
    QObject,
    QThread,
    Qt,
    Signal,
    Slot,
)

from qt_dicom_viewer.core.dicom_models import RenderRequest, RenderResult
from qt_dicom_viewer.ui.state.series_catalog import SeriesCatalog
from qt_dicom_viewer.ui.workers.dicom_render_worker import DicomRenderWorker



logger = logging.getLogger(__name__)

class RenderService(QObject):
    renderRequested = Signal(object)
    rendered = Signal(object)
    failed = Signal(object)

    def __init__(
        self,
        series_catalog: SeriesCatalog,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        logger.info("Starting render service")

        self._thread = QThread(self)

        # Worker 不能设置 parent，因为稍后需要 moveToThread()
        self._worker = DicomRenderWorker(
            series_catalog,
        )
        self._worker.moveToThread(self._thread)

        self.renderRequested.connect(self._worker.handleRenderRequest)

        # 转发 Worker 的结果
        self._worker.render_finished.connect(self.handleRenderFinished)
        self._worker.render_failed.connect(self.failed)

        self._thread.finished.connect(
            self._worker.deleteLater
        )

        self._thread.start()

    @Slot(object)
    def handleRenderFinished(self, result: RenderResult) -> None:
        self.rendered.emit(result)

    def submit(self, request: RenderRequest) -> None:
        logger.info(f"Submitting render request: {request.request_id}")
        self.renderRequested.emit(request)

    @Slot()
    def shutdown(self) -> None:
        if not self._thread.isRunning():
            return
        logger.info("Stopping render service")
        self._thread.quit()
        self._thread.wait()

        logger.info("Render service stopped")