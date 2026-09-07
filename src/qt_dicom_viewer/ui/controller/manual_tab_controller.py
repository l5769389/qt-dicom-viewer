"""Offline operation manual and reading state owned by its workspace tab."""
import json
import math
from functools import lru_cache
from importlib.resources import files

from PySide6.QtCore import Property, Signal, Slot

from qt_dicom_viewer.model import TabType
from qt_dicom_viewer.ui.controller.utility_tab_controller import UtilityTabController


@lru_cache(maxsize=1)
def manual_content():
    return json.loads(files("qt_dicom_viewer").joinpath("qml/assets/help/manual.json").read_text(encoding="utf-8"))


class ManualTabController(UtilityTabController):
    chapterChanged = Signal()
    navigationChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(TabType.MANUAL, "操作手册", parent)
        self._content = manual_content()
        self._chapters = {c["id"]: c for c in self._content["chapters"]}
        self._chapter = "quick-start"
        self._search = ""
        self._positions = {}

    @Property(str, notify=chapterChanged)
    def chapterId(self):
        return self._chapter

    @Property("QVariantMap", notify=chapterChanged)
    def currentChapter(self):
        chapter = self._chapters[self._chapter]
        category = next(c for c in self._content["categories"] if c["id"] == chapter["category"])
        return dict(chapter, categoryTitle=category["title"])

    @Property(str, notify=navigationChanged)
    def search(self):
        return self._search

    @Slot(str)
    def setSearch(self, value):
        if self._search != value:
            self._search = value
            self.navigationChanged.emit()

    @Property("QVariantList", notify=navigationChanged)
    def navigation(self):
        query = self._search.strip().casefold()
        rows = []
        for category in self._content["categories"]:
            chapters = [c for c in self._content["chapters"] if c["category"] == category["id"]
                        and (not query or query in json.dumps(c, ensure_ascii=False).casefold()
                             or query in category["title"].casefold())]
            if chapters:
                rows.append(dict(category, chapters=[dict(id=c["id"], title=c["title"]) for c in chapters]))
        return rows

    @Slot(str)
    def selectChapter(self, chapter_id):
        if chapter_id not in self._chapters:
            chapter_id = "quick-start"
        self._chapter = chapter_id
        self._positions[chapter_id] = 0.0
        self.chapterChanged.emit()

    @Property(float, notify=chapterChanged)
    def scrollPosition(self):
        return self._positions.get(self._chapter, 0.0)

    @Slot(float)
    def setScrollPosition(self, value):
        if math.isfinite(value):
            self._positions[self._chapter] = max(0.0, value)
