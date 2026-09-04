from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from qt_dicom_viewer.core.volume_manager import VolumeManager
from qt_dicom_viewer.model import DicomSeriesRecord
from qt_dicom_viewer.service.render_serivce import RenderService
from qt_dicom_viewer.ui.controller.panel_controller import  PanelController
from qt_dicom_viewer.ui.controller.workspace_controller import WorkspaceController
from qt_dicom_viewer.application.series_catalog import SeriesCatalog


class AppController(QObject):
    statusMessageChanged = Signal()
    scanningChanged = Signal()
    summaryTextChanged = Signal()
    seriesItemsChanged = Signal()

    def __init__(self,image_provider) -> None:
        super().__init__()
        self._status_message = "Ready"
        self._image_provider = image_provider
        self._summary_text = "No DICOM folder loaded"
        self._series_items = []
        self._series_info: dict[str, DicomSeriesRecord] = {}
        self._series_catalog = SeriesCatalog()
        self._workspace_controller = WorkspaceController(self._series_catalog,self._image_provider,parent= self)
        self._panel_controller = PanelController(parent=self, series_catalog=self._series_catalog, image_provider=image_provider)
        self._volume_manager = VolumeManager()
        self.render_service = RenderService(self._series_catalog, self._volume_manager, self)
        self._signal_connect()


    def _signal_connect(self):
        #  监听切换series
        self._panel_controller.tabCreateRequested.connect(
            self._workspace_controller.activeWorkspace
        )
        # renderService接收渲染请求。
        self._workspace_controller.renderRequested.connect(
            self.render_service.submit
        )
        # workspace接收渲染结果
        self.render_service.rendered.connect(
            self._workspace_controller.handleRenderResult
        )
        self.render_service.failed.connect(
            self._workspace_controller.handleRenderFailure
        )


    @Property(QObject, constant=True)
    def panelController(self) -> QObject:
        return self._panel_controller

    @Slot()
    def shutdown(self) -> None:
        self._panel_controller.shutdown()
        self._workspace_controller.shutdown()
        self.render_service.shutdown()

    @Property(QObject, constant=True)
    def workspaceController(self) -> QObject:
        return self._workspace_controller
