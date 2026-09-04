from __future__ import annotations

from dataclasses import dataclass, replace
import math
from math import isfinite
from uuid import uuid4

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtGui import QColor

from qt_dicom_viewer.model.dicom_types import FrameDisplayMeta


@dataclass(frozen=True, slots=True)
class TextAnnotation:
    annotation_id: str
    slice_index: int
    column: float
    row: float
    text: str
    color: str
    font_size: int
    frame_key: tuple


class TextAnnotationController(QObject):
    annotationsChanged = Signal()
    editorChanged = Signal()
    selectionChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._annotations: dict[str, TextAnnotation] = {}
        self._current_slice: int | None = None
        self._frame_key: tuple | None = None
        self._selected_id = ""
        self._text = "标注"
        self._color = "#ffd45c"
        self._font_size = 16

    def set_current_slice(self, slice_index: int | None) -> None:
        if slice_index == self._current_slice:
            return
        self._current_slice = slice_index
        selected = self._annotations.get(self._selected_id)
        if selected is not None and selected.slice_index != slice_index:
            self._selected_id = ""
            self.selectionChanged.emit()
            self.editorChanged.emit()
        self.annotationsChanged.emit()

    def set_frame(self, series_uid: str, frame: FrameDisplayMeta) -> None:
        geometry = frame.geometry
        pose = (
            geometry.pixel_spacing.row,
            geometry.pixel_spacing.column,
            *(geometry.image_position_patient or ()),
            *(geometry.image_orientation_patient or ()),
        )
        frame_key = (
            series_uid,
            frame.instance_meta.sop_instance_uid,
            frame.slice_index,
            geometry.rows,
            geometry.columns,
            tuple(
                round(value, 7)
                if isinstance(value, (int, float)) and math.isfinite(value)
                else str(value)
                for value in pose
            ),
        )
        if frame_key == self._frame_key and frame.slice_index == self._current_slice:
            return
        self._frame_key = frame_key
        self.set_current_slice(frame.slice_index)
        self.clearSelection()
        self.annotationsChanged.emit()

    @Property("QVariantList", notify=annotationsChanged)
    def annotationItems(self) -> list[dict]:
        return [
            {
                "annotationId": annotation.annotation_id,
                "sliceIndex": annotation.slice_index,
                "column": annotation.column,
                "row": annotation.row,
                "text": annotation.text,
                "color": annotation.color,
                "fontSize": annotation.font_size,
                "selected": annotation.annotation_id == self._selected_id,
            }
            for annotation in self._annotations.values()
            if annotation.slice_index == self._current_slice
            and annotation.frame_key == self._frame_key
        ]

    @Property(str, notify=editorChanged)
    def annotationText(self) -> str:
        return self._text

    @Property(str, notify=editorChanged)
    def annotationColor(self) -> str:
        return self._color

    @Property(int, notify=editorChanged)
    def annotationFontSize(self) -> int:
        return self._font_size

    @Property(str, notify=selectionChanged)
    def selectedAnnotationId(self) -> str:
        return self._selected_id

    @Property(bool, notify=selectionChanged)
    def hasSelection(self) -> bool:
        return self._selected_id in self._annotations

    @Property(bool, notify=annotationsChanged)
    def hasAnnotations(self) -> bool:
        return bool(self._annotations)

    def _update_selected(self, **changes) -> None:
        selected = self._annotations.get(self._selected_id)
        if selected is None:
            return
        updated = replace(selected, **changes)
        if updated == selected:
            return
        self._annotations[selected.annotation_id] = updated
        self.annotationsChanged.emit()

    @Slot(str)
    def setAnnotationText(self, text: str) -> None:
        text = str(text)[:200]
        if text == self._text:
            return
        self._text = text
        self._update_selected(text=text)
        self.editorChanged.emit()

    @Slot(str)
    def setAnnotationColor(self, color: str) -> None:
        value = QColor(color)
        if not value.isValid():
            return
        color = value.name()
        if color == self._color:
            return
        self._color = color
        self._update_selected(color=color)
        self.editorChanged.emit()

    @Slot(int)
    def setAnnotationFontSize(self, size: int) -> None:
        size = max(10, min(int(size), 48))
        if size == self._font_size:
            return
        self._font_size = size
        self._update_selected(font_size=size)
        self.editorChanged.emit()

    @Slot(float, float)
    def addAnnotation(self, column: float, row: float) -> None:
        if (
            self._current_slice is None
            or not isfinite(column)
            or not isfinite(row)
            or not self._text.strip()
            or self._frame_key is None
        ):
            return
        annotation = TextAnnotation(
            annotation_id=str(uuid4()),
            slice_index=self._current_slice,
            column=float(column),
            row=float(row),
            text=self._text.strip(),
            color=self._color,
            font_size=self._font_size,
            frame_key=self._frame_key,
        )
        self._annotations[annotation.annotation_id] = annotation
        self._selected_id = annotation.annotation_id
        self.annotationsChanged.emit()
        self.selectionChanged.emit()

    @Slot(str)
    def selectAnnotation(self, annotation_id: str) -> None:
        annotation = self._annotations.get(annotation_id)
        if (
            annotation is None
            or annotation.slice_index != self._current_slice
            or annotation.frame_key != self._frame_key
        ):
            return
        selection_changed = annotation_id != self._selected_id
        self._selected_id = annotation_id
        editor_changed = (
            self._text != annotation.text
            or self._color != annotation.color
            or self._font_size != annotation.font_size
        )
        self._text = annotation.text
        self._color = annotation.color
        self._font_size = annotation.font_size
        if selection_changed:
            self.selectionChanged.emit()
            self.annotationsChanged.emit()
        if editor_changed:
            self.editorChanged.emit()

    @Slot()
    def clearSelection(self) -> None:
        if not self._selected_id:
            return
        self._selected_id = ""
        self.selectionChanged.emit()
        self.annotationsChanged.emit()

    @Slot()
    def deleteSelected(self) -> None:
        if self._selected_id not in self._annotations:
            return
        del self._annotations[self._selected_id]
        self._selected_id = ""
        self.annotationsChanged.emit()
        self.selectionChanged.emit()

    @Slot()
    def clearAll(self) -> None:
        if not self._annotations:
            return
        self._annotations.clear()
        self._selected_id = ""
        self.annotationsChanged.emit()
        self.selectionChanged.emit()
