import logging
import uuid
from types import MappingProxyType

from PySide6.QtCore import QObject, Signal, Slot, Property

from qt_dicom_viewer.model import TabConfig, ViewportConfig, SeriesDisplayMeta, TabType, MprPlane, TwoDViewType
from qt_dicom_viewer.ui.controller.tab.tool_controller import ToolController
from qt_dicom_viewer.ui.controller.viewport.viewport_controller import ViewportController



logger = logging.getLogger(__name__)
class TabController(QObject):
    renderRequested = Signal(object)
    activeToolChanged = Signal(object)
    activeViewportChanged = Signal()

    def __init__(self, tab_config: TabConfig,parent = None):
        super().__init__(parent)
        self._tab_config = tab_config
        self._viewport_dict: dict[str, ViewportController] = {}
        self._create_tool_controller()
        self._series_by_uid: dict[str, SeriesDisplayMeta] = {
            meta.series_uid: meta
            for meta in tab_config.series_metas
        }
        self._active_viewport_id: str = ''
        self._create_viewport_dict()

    @Property(str, notify=activeToolChanged)
    def activeTool(self):
        return self._tool_controller.activeTool


    @Property(QObject, notify=activeViewportChanged)
    def activeViewport(self):
        if self._active_viewport_id == '':
            return None
        return self._viewport_dict.get(self._active_viewport_id)

    @Property(QObject,constant= True)
    def toolController(self) -> QObject:
        return self._tool_controller


    def _create_tool_controller(self) -> None:
        self._tool_controller = ToolController(
            parent=self
        )


    def init_render(self):
        for viewport in self._viewport_dict.values():
            viewport.request_first_loader()


    # MappingProxyType 可以防止 Workspace 意外修改 Tab 内部字典：
    @property
    def viewports_by_id(self) -> MappingProxyType[str,ViewportController]:
        return MappingProxyType(
            self._viewport_dict
        )

    def _create_viewport_dict(self) -> None:
        match self._tab_config.tab_type:
            case TabType.TWO_D:
                for series_meta in self._tab_config.series_metas:
                    viewport_id = str(uuid.uuid4())
                    self._active_viewport_id = viewport_id
                    viewport = ViewportController(
                        viewport_config=ViewportConfig(
                            viewport_id,
                            tab_id=self._tab_config.tab_id,
                            viewport_type=TwoDViewType.STACK,
                            series_uid=series_meta.series_uid,
                            series_meta=series_meta,
                        ),
                        tool_controller=self._tool_controller,
                        parent=self
                    )
                    self.connect_signal(viewport)
                    self._viewport_dict[viewport_id] = viewport
            case TabType.MPR:
                    for series_meta in self._tab_config.series_metas:
                        for view_type in [MprPlane.AXIAL, MprPlane.SAGITTAL, MprPlane.CORONAL]:
                            viewport_id = str(uuid.uuid4())
                            if view_type == MprPlane.AXIAL:
                                self._active_viewport_id = viewport_id
                            viewport = ViewportController(
                                viewport_config=ViewportConfig(
                                    viewport_id,
                                    tab_id=self._tab_config.tab_id,
                                    viewport_type=view_type,
                                    series_uid=series_meta.series_uid,
                                    series_meta=series_meta,
                                ),
                                tool_controller=self._tool_controller,
                                parent=self
                            )
                            self.connect_signal(viewport)
                            self._viewport_dict[viewport_id] = viewport


    def connect_signal(self, viewport: ViewportController):
        viewport.renderRequested.connect(
            self.renderRequested.emit
        )

    @property
    def tab_config(self) -> TabConfig:
        return self._tab_config


    @Slot(str)
    def activateViewport(self, activeViewportId: str) -> None:
        if activeViewportId not in self._viewport_dict:
            logger.warning(
                "Cannot activate unknown viewport: viewport_id=%s",
                activeViewportId,
            )
            return

        if self._active_viewport_id == activeViewportId:
            return

        self._active_viewport_id = activeViewportId
        self.activeViewportChanged.emit()
