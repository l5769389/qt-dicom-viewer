import logging

from PySide6.QtCore import QObject, Slot, Property, Signal

from qt_dicom_viewer.model import (
    RenderFailure,
    RenderRequest,
    RenderResult,
    TabConfig,
    TabType,
    WindowLevel,
)
from qt_dicom_viewer.ui.controller.tab.tab_controller import TabController
from qt_dicom_viewer.ui.controller.tab.tag_controller import TagController
from qt_dicom_viewer.service.tag_read_service import TagReadService
from qt_dicom_viewer.ui.controller.viewport.viewport_controller import ViewportController
from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
from qt_dicom_viewer.application.series_catalog import SeriesCatalog
from qt_dicom_viewer.model.render_models import VolumeLoadResult
from qt_dicom_viewer.model.render_models import PetBatchRenderResult
from qt_dicom_viewer.ui.controller.tab.pet_workspace_controller import PetWorkspaceController

from qt_dicom_viewer.ui.controller.utility_tab_controller import UtilityTabController

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
        self._tab_dict:dict[str, TabController | UtilityTabController] = {}
        self._active_tab_id: str | None = None
        self._tab_mru: list[str] = []
        self._image_provider = image_provider
        self._tag_read_service = TagReadService(self)

    @Slot()
    def openSettings(self):
        self._open_utility(TabType.SETTINGS, "设置")

    @Slot()
    def openDataSources(self):
        settings = getattr(self.parent(), "_settings_controller", None)
        if settings is not None:
            settings.selectCategory("sources")
        self.openSettings()

    @Slot()
    def openPacs(self):
        self._open_utility(TabType.PACS, "PACS 浏览器")

    def _open_utility(self, tab_type, label):
        tab_id = f"workspace-{tab_type.value}"
        if tab_id not in self._tab_dict:
            self._tab_dict[tab_id] = UtilityTabController(tab_type, label, self)
            self.tabsChanged.emit()
        self.activateTabId(tab_id)

    @Slot(str)
    def closeTab(self, tab_id: str):
        if tab_id not in self._tab_dict:
            return
        tab = self._tab_dict.pop(tab_id)
        tab.dispose()
        tab.deleteLater()
        self._tab_mru = [key for key in self._tab_mru if key != tab_id]
        if tab_id == self._active_tab_id:
            self._active_tab_id = self._tab_mru[0] if self._tab_mru else ""
            self.activeTabChanged.emit()
            self.activeViewportChanged.emit()
        self.tabsChanged.emit()

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

        current_tab = self._tab_dict.get(self._active_tab_id)
        if current_tab is not None:
            current_tab.pausePlayback()
        self._active_tab_id = tab_id
        self._tab_mru = [tab_id] + [key for key in self._tab_mru if key != tab_id]
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
    def activeTab(self) -> TabController | UtilityTabController | None:
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
        if tab_type in (TabType.SETTINGS, TabType.PACS):
            return
        tab, created = self._create_or_activate_tab(
            series_uid,
            tab_label,
            tab_type,
        )
        if created and tab is not None:
            if tab.tagController is not None:
                tab.tagController.start()
            else:
                tab.init_render()

    def _create_or_activate_tab(
        self,
        series_uid: str,
        tab_label: str,
        tab_type: TabType,
    ) -> tuple[TabController | None, bool]:
        tab_id = f'{series_uid}_{tab_type}'
        if tab_id == self._active_tab_id:
            return self._tab_dict.get(tab_id), False
        new_tab = None
        if tab_id not in self._tab_dict:
            series = self._series_catalog.get_series(series_uid)
            if series is None:
                logger.warning(
                    "Cannot create tab for unknown series: series_uid=%s",
                    series_uid,
                )
                return None, False
            if tab_type == TabType.FOUR_D and not series.supports_four_d:
                logger.warning(
                    "Cannot create 4D tab for unsupported series: "
                    "series_uid=%s",
                    series_uid,
                )
                return None, False
            series_display_meta = self._series_catalog.get_series_display_meta(series_uid)
            if series_display_meta is None:
                logger.warning(
                    "Cannot create tab for unknown series: series_uid=%s",
                    series_uid,
                )
                return None, False

            tab_config = TabConfig(
                tab_id = tab_id,
                tab_label = tab_label,
                tab_type = tab_type,
                series_metas=(series_display_meta,),
            )

            tag_controller = None
            if tab_type == TabType.TAG:
                tag_controller = TagController(
                    tab_id, self._series_catalog.get_series(series_uid),
                    self._tag_read_service,
                )
            if tab_type == TabType.MPR and series_display_meta.modality.upper() == "PT":
                new_tab = PetWorkspaceController(tab_config,
                    pet_series=self._series_catalog.get_series(series_uid), parent=self)
            else:
                new_tab = TabController(tab_config, parent=self, tag_controller=tag_controller)
            self.connect_signal(new_tab)
            self._tab_dict[tab_id] = new_tab

        tab = new_tab or self._tab_dict[tab_id]

        self.tabsChanged.emit()
        self.activateTabId(tab_id)
        return tab, new_tab is not None


    @Slot()
    def shutdown(self) -> None:
        for tab in self._tab_dict.values():
            tab.dispose()
        self._tag_read_service.shutdown()

    def connect_signal(self, tab: TabController):
        tab.renderRequested.connect(
            self.renderRequested.emit
        )
        tab.activeViewportChanged.connect(
            self.activeViewportChanged.emit
        )
        tab.imageRemovalRequested.connect(
            self._image_provider.remove_image
        )
        tab.stackNavigationRequested.connect(
            self.openSeriesSlice
        )

    def _find_tab_by_viewport_id(
            self,
            viewport_id: str,
    ) -> TabController | None:
        for tab in self._tab_dict.values():
            if tab.contains_viewport(viewport_id):
                return tab

        return None

    @Slot(object)
    def handleRenderResult(self, result: RenderResult):
        logger.debug(
            "Receive render result: viewport_id=%s",
            result.viewport_id,
        )
        tab = self._find_tab_by_viewport_id(result.viewport_id)
        if tab is None:
            logger.debug(
                "Discard render result for unknown or closed viewport: "
                "viewport_id=%s",
                result.viewport_id,
            )
            return

        if not tab.accepts_render_result(result):
            logger.debug(
                "Discard stale render result before updating image provider: "
                "request_id=%s viewport_id=%s",
                result.response_id,
                result.viewport_id,
            )
            return

        if isinstance(result, PetBatchRenderResult):
            for frame in result.frames:
                if frame.image is not None:
                    self._image_provider.set_array(frame.viewport_id, frame.image)
        elif not isinstance(result, VolumeLoadResult) and result.image is not None:
            image_key = getattr(result, "image_key", result.viewport_id)
            self._image_provider.set_array(image_key, result.image)

        tab.handleRenderResult(result)

    @Slot(str, str)
    def createFusionTab(self, ct_uid, pet_uid):
        ct = self._series_catalog.get_series(ct_uid)
        pet = self._series_catalog.get_series(pet_uid)
        if ct is None or pet is None or ct.modality.upper() != "CT" or pet.modality.upper() != "PT":
            return
        tab_id = f"petct:{ct_uid}:{pet_uid}"
        if tab_id in self._tab_dict:
            self.activateTabId(tab_id)
            return
        config = TabConfig(tab_id=tab_id, tab_label=f"{ct.patient_name} · PET/CT",
            tab_type=TabType.PETCT_FUSION, series_metas=(
                self._series_catalog.get_series_display_meta(ct_uid),
                self._series_catalog.get_series_display_meta(pet_uid)))
        tab = PetWorkspaceController(config, ct_series=ct, pet_series=pet, parent=self)
        self.connect_signal(tab)
        self._tab_dict[tab_id] = tab
        self.tabsChanged.emit()
        self.activateTabId(tab_id)
        tab.init_render()

    @Slot(object)
    def handleRenderFailure(self, failure: RenderFailure) -> None:
        tab = self._find_tab_by_viewport_id(failure.viewport_id)
        if tab is None:
            return
        tab.handleRenderFailure(failure)

    @Slot(str, int, float, float, bool)
    def openSeriesSlice(
        self,
        series_uid: str,
        slice_index: int,
        window_center: float,
        window_width: float,
        inverted: bool,
    ) -> None:
        series = self._series_catalog.get_series(series_uid)
        if series is None:
            return
        tab, _ = self._create_or_activate_tab(
            series_uid,
            series.patient_name,
            TabType.TWO_D,
        )
        if tab is None:
            return
        tab.navigate_stack(
            slice_index,
            WindowLevel(
                center=float(window_center),
                width=max(float(window_width), 1.0),
            ),
            bool(inverted),
        )


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
