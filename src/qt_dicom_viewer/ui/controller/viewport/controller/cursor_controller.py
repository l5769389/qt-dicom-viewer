import logging

from PySide6.QtCore import QObject, Signal, Property, Slot

from qt_dicom_viewer.model import ViewportConfig, PointerDisplayMeta
from qt_dicom_viewer.utils.utils import _display_number
logger = logging.getLogger(__name__)

class CursorController(QObject):
    cursorInfoChanged = Signal()

    def __init__(self,viewport_config:ViewportConfig, parent=None):
        super().__init__(parent)
        self.viewport_config = viewport_config
        self._pointer_meta: PointerDisplayMeta | None = None


    @Property(
        "QVariantMap",
        notify=cursorInfoChanged,
    )
    def cursorInfo(self) -> dict:
        pointer = self._pointer_meta

        if pointer is None:
            return {
                "inside": False,
                "x": "--",
                "y": "--",
                "value": "--",
                "unit": "",
            }

        return {
            "inside": True,
            "x": _display_number(
                pointer.pointer_x,
                precision=0,
            ),
            "y": _display_number(
                pointer.pointer_y,
                precision=0,
            ),
            "value": _display_number(
                pointer.pointer_ct_value,
                precision=1,
            ),
            "unit": (
                "HU"
                if self.viewport_config.series_meta.modality
                   == "CT"
                else ""
            ),
        }

    @Slot(float, float)
    def updatePosition(
        self,
        column: float,
        row: float,
        ct_value: float,
    ) -> None:
        logger.debug(f'updateCursorPosition,{column},{row}')
        self._pointer_meta = PointerDisplayMeta(
            pointer_x=column,
            pointer_y=row,
            pointer_ct_value=ct_value
        )
        self.cursorInfoChanged.emit()