import logging
import uuid
from types import MappingProxyType

from PySide6.QtCore import QObject, Signal

from qt_dicom_viewer.core.dicom_models import TabConfig, ViewportConfig, SeriesDisplayMeta
from qt_dicom_viewer.ui.controller.tab.tool_controller import ToolController
from qt_dicom_viewer.ui.controller.viewport.viewport_controller import ViewportController

logger = logging.getLogger(__name__)
class TabController(QObject):
    renderRequested = Signal(object)

    def __init__(self, tab_config: TabConfig,parent = None):
        super().__init__(parent)
        self._tab_config = tab_config
        self._viewport_dict: dict[str, ViewportController] = {}
        self._create_tool_controller()
        self._series_by_uid: dict[str, SeriesDisplayMeta] = {
            meta.series_uid: meta
            for meta in tab_config.series_metas
        }
        self._create_viewport_dict()

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
        for series_meta in self._tab_config.series_metas:
            viewport_id = str(uuid.uuid4())
            viewport = ViewportController(
                viewport_config=ViewportConfig(
                    viewport_id,
                    tab_id=self._tab_config.tab_id,
                    viewport_type="",
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
