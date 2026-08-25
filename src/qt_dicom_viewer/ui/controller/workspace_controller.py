import logging

from PySide6.QtCore import QObject, Slot, Property, Signal

from qt_dicom_viewer.model import TabConfig, TabType, RenderRequest, RenderResult
from qt_dicom_viewer.ui.controller.tab.tab_controller import TabController
from qt_dicom_viewer.ui.controller.viewport.viewport_controller import ViewportController
from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
from qt_dicom_viewer.application.series_catalog import SeriesCatalog

logger = logging.getLogger(__name__)

class WorkspaceController(QObject):
    tabsChanged = Signal()
    activeTabChanged = Signal()
    activeViewportChanged = Signal()

    rendered = Signal()
    renderRequested = Signal(object)

    def __init__(self,
                 series_catalog: SeriesCatalog,
                 image_provider:DicomImageProvider,
                 parent = None):
        super().__init__(parent)
        self._series_catalog = series_catalog
        self._tab_dict:dict[str, TabController] = {}
        self._active_tab_id: str | None = None
        self._image_provider = image_provider
        # workspace 直接关联的viewport
        self._viewport_dict: dict[str, ViewportController] = {}

    @Slot(str)
    def closeTab(self, tab_id: str):
        if tab_id in self._tab_dict:
            tab = self._tab_dict[tab_id]
            self.unregister_viewport(tab)
            tab.deleteLater()
            del self._tab_dict[tab_id]
        if tab_id == self._active_tab_id:
            self._active_tab_id = next(iter(self._tab_dict), "")
        self.tabsChanged.emit()
        self.activeTabChanged.emit()
        self.activeViewportChanged.emit()

    @Slot(str)
    def submit(self, render_request: RenderRequest):
        pass

    @Property(
        "QVariantList",
        notify=activeTabChanged,
    )
    def currentTabAllViewports(self) -> list[QObject]:
        if self._active_tab_id is None:
            return []

        tab = self._tab_dict.get(
            self._active_tab_id
        )

        if tab is None:
            return []

        return list(
            tab.viewports_by_id.values()
        )


    @Property(
        QObject,
        notify=activeViewportChanged,
    )
    def activeViewport(self) -> QObject | None:
        if self._active_tab_id is None:
            return None

        tab = self._tab_dict.get(
            self._active_tab_id
        )

        if tab is None:
            return None

        return tab.activeViewport


    @Slot(str)
    def activateTabId(self, tab_id: str):
        if tab_id not in self._tab_dict:
            return

        if tab_id == self._active_tab_id:
            return

        self._active_tab_id = tab_id
        self.activeTabChanged.emit()
        self.activeViewportChanged.emit()


    @Property("QVariantList", notify=tabsChanged)
    def tabs(self):
        return [{
            "tabId": each_tab.tab_config.tab_id,
            "tabLabel": each_tab.tab_config.tab_label,
            "tabType": each_tab.tab_config.tab_type,
        } for each_tab in self._tab_dict.values()]

    @Property(str, notify=activeTabChanged)
    def activeTabId(self) -> str | None:
        return self._active_tab_id

    @Property(QObject,notify=activeTabChanged)
    def activeTab(self) -> TabController | None:
        return self._tab_dict.get(self._active_tab_id, None)

    @Property(str, notify=activeTabChanged)
    def activeTabType(self) -> str:
        tab = self._tab_dict.get(self._active_tab_id)

        if tab is None:
            return ""

        return tab.tab_config.tab_type.value


    @Slot(str, str, str)
    def createTab(self,series_uid: str,
                        tab_label: str,
                        tab_type: TabType
                   ):
        tab_id = f'{series_uid}_{tab_type}'
        if tab_id == self._active_tab_id:
            return
        new_tab = None
        if tab_id not in self._tab_dict:
            series_display_meta = self._series_catalog.get_series_display_meta(series_uid)
            if series_display_meta is None:
                logger.warning(
                    "Cannot create tab for unknown series: series_uid=%s",
                    series_uid,
                )
                return

            tab_config = TabConfig(
                tab_id = tab_id,
                tab_label = tab_label,
                tab_type = tab_type,
                series_metas=(series_display_meta,),
            )

            new_tab = TabController(tab_config ,parent= self)
            self.register_viewport(new_tab)
            self.connect_signal(new_tab)
            self._tab_dict[tab_id] = new_tab

        self._active_tab_id = tab_id
        self.tabsChanged.emit()
        self.activeTabChanged.emit()
        self.activeViewportChanged.emit()

        # QML 已能访问 active viewport 后再发起首帧请求。
        if new_tab is not None:
            new_tab.init_render()



    def unregister_viewport(self, tab: TabController):
        for viewport_id, viewport in tab.viewports_by_id.items():
            self._viewport_dict.pop(viewport_id, None)
            self._image_provider.remove_image(viewport_id)

    def register_viewport(self, new_tab: TabController):
        for viewport_id, viewport in new_tab.viewports_by_id.items():
            self._viewport_dict[viewport_id] = viewport

    def connect_signal(self, tab: TabController):
        tab.renderRequested.connect(
            self.renderRequested.emit
        )
        tab.activeViewportChanged.connect(
            self.activeViewportChanged.emit
        )

    @Slot(object)
    def handleRenderResult(self, result: RenderResult):
        logger.debug(f'receive render result={result.viewport_id}')
        if result.image is not None:
            self._image_provider.set_array(result.viewport_id, result.image)
        viewport = self._viewport_dict.get(result.viewport_id, None)
        if viewport is not None:
            viewport.handleRenderResult(result)


    @Slot(str, str)
    def activeWorkspace(self, series_uid: str, tab_type_value: str):
        try:
            tab_type = TabType(tab_type_value)
        except ValueError:
            logger.warning(
                "Unsupported tab type: %s",
                tab_type_value,
            )
            return
        series = self._series_catalog.get_series(series_uid)
        if series is None:
            return
        label = f'{series.patient_name}'
        self.createTab(series_uid,label,tab_type)
