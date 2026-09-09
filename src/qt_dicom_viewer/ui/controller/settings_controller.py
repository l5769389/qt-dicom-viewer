"""One workspace settings object shared by all tabs and viewports."""
from copy import deepcopy
import json
from pathlib import Path
import uuid

from PySide6.QtCore import QObject, Property, Signal, Slot, QStandardPaths, QSaveFile, QIODevice
from PySide6.QtWidgets import QFileDialog

from qt_dicom_viewer import __version__
from qt_dicom_viewer.core.color_maps import COLOR_MAPS
from qt_dicom_viewer.preset import CT_WINDOW_PRESETS
from qt_dicom_viewer.settings.preferences import DEFAULTS, CORNER_FIELDS, CORNERS, METRICS, normalize_settings, validate_value


class SettingsController(QObject):
    categoryChanged = Signal()
    changed = Signal()
    sectionChanged = Signal(str)
    messageChanged = Signal()

    def __init__(self, parent=None, *, path=None):
        super().__init__(parent)
        self._path = None if path is False else Path(path) if path else Path(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)) / "display-settings.json"
        self._active_category = "sources"
        self._data = deepcopy(DEFAULTS)
        self._message = ""
        if self._path and self._path.exists():
            try:
                self._data = normalize_settings(json.loads(self._path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                self._message = "读取显示设置失败，已使用默认值。"

    @Property(str, constant=True)
    def applicationVersion(self):
        return __version__

    @Property(str, notify=categoryChanged)
    def activeCategory(self):
        return self._active_category

    @Slot(str)
    def selectCategory(self, category):
        if category in ("sources", *DEFAULTS) and category != self._active_category:
            self._active_category = category
            self.categoryChanged.emit()

    @Property("QVariantMap", notify=changed)
    def values(self):
        return deepcopy(self._data)

    @Property(str, notify=messageChanged)
    def message(self):
        return self._message

    @Property(str, constant=True)
    def defaultExportDirectory(self):
        documents = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        return str((Path(documents) if documents else Path.home() / "Documents") / "Voxenra" / "Exports")

    @Property(str, notify=changed)
    def exportDirectory(self):
        return self._data["export"]["directory"] or self.defaultExportDirectory

    @Slot()
    def chooseExportDirectory(self):
        folder = QFileDialog.getExistingDirectory(None, "选择导出目录", self.exportDirectory)
        if folder:
            self.setValue("export", "directory", folder)

    @Property("QVariantList", constant=True)
    def colorMaps(self):
        from qt_dicom_viewer.core.pseudocolor import color_lut
        return [dict(key=k, label=label, colors=["#{:02x}{:02x}{:02x}".format(*rgb)
                    for rgb in color_lut(k)]) for k, (label, _) in COLOR_MAPS.items()]

    @Property("QVariantList", constant=True)
    def cornerFields(self):
        return [dict(key=k, label=v) for k, v in CORNER_FIELDS.items()]

    @Property("QVariantList", constant=True)
    def roiFields(self):
        return [dict(key=k, label=v) for k, v in METRICS.items()]

    @Property("QVariantList", notify=changed)
    def windowTemplates(self):
        builtins = [dict(presetId=p.preset_id, label=p.label, center=p.center, width=p.width,
                         enabled=p.preset_id not in self._data["window"]["hidden"], builtin=True) for p in CT_WINDOW_PRESETS]
        return builtins + [dict(p, builtin=False) for p in self._data["window"]["custom"]]

    @property
    def window_presets(self):
        return [p for p in self.windowTemplates if p["enabled"]]

    def section(self, name):
        return deepcopy(self._data[name])

    def _error(self, message):
        self._message = message
        self.messageChanged.emit()
        return False

    def _commit(self, section, candidate):
        if self._path:
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                target = QSaveFile(str(self._path))
                payload = json.dumps({"schemaVersion": 1, **candidate}, ensure_ascii=False, indent=2).encode("utf-8")
                if not target.open(QIODevice.WriteOnly) or target.write(payload) != len(payload) or not target.commit():
                    raise OSError("Cannot save settings")
            except OSError:
                return self._error("保存设置失败，请检查配置目录是否可写。")
        self._data = candidate
        self._error("")
        self.changed.emit()
        self.sectionChanged.emit(section)
        return True

    @Slot(str, str, "QVariant", result=bool)
    def setValue(self, section, key, value):
        # Compatibility for callers using the former individual dimension keys.
        if section == "roi" and key in ("width", "height"):
            key = "dimensions"
        if hasattr(value, "toVariant"):
            value = value.toVariant()
        try:
            value = validate_value(section, key, value)
        except (ValueError, TypeError) as exc:
            return self._error(str(exc))
        if value == self._data[section][key]:
            self._error("")
            return True
        candidate = deepcopy(self._data)
        candidate[section][key] = value
        return self._commit(section, candidate)

    @Slot(str, result=bool)
    def resetSection(self, section):
        if section not in DEFAULTS:
            return self._error("未知设置分类")
        candidate = deepcopy(self._data)
        candidate[section] = deepcopy(DEFAULTS[section])
        return self._commit(section, candidate)

    @Slot(str, str, float, float, result=bool)
    def saveWindowTemplate(self, identifier, label, width, center):
        templates = self.section("window")["custom"]
        item = dict(presetId=identifier or "custom-" + str(uuid.uuid4()), label=label, width=width, center=center, enabled=True)
        if identifier:
            if not any(p["presetId"] == identifier for p in templates):
                return self._error("找不到自定义模板")
            templates = [dict(item, enabled=p["enabled"]) if p["presetId"] == identifier else p for p in templates]
        else:
            templates.append(item)
        return self.setValue("window", "custom", templates)

    @Slot(str, result=bool)
    def deleteWindowTemplate(self, identifier):
        return self.setValue("window", "custom", [p for p in self._data["window"]["custom"] if p["presetId"] != identifier])

    @Slot(str, bool, result=bool)
    def enableWindowTemplate(self, identifier, enabled):
        if identifier in {p.preset_id for p in CT_WINDOW_PRESETS}:
            hidden = [i for i in self._data["window"]["hidden"] if i != identifier]
            if not enabled:
                hidden.append(identifier)
            return self.setValue("window", "hidden", hidden)
        return self.setValue("window", "custom", [dict(p, enabled=enabled) if p["presetId"] == identifier else p for p in self._data["window"]["custom"]])

    @Slot(str, str, result=bool)
    def addCornerField(self, corner, field):
        if corner not in CORNERS or field not in CORNER_FIELDS:
            return self._error("无效的四角信息项")
        entries = self._data["corners"][corner]
        if field in entries:
            return self._error("该角落已经包含此项")
        return self.setValue("corners", corner, entries + [field])

    @Slot(str, int, int, result=bool)
    def moveCornerField(self, corner, index, offset):
        if corner not in CORNERS:
            return False
        entries = list(self._data["corners"][corner])
        dest = index + offset
        if not 0 <= index < len(entries) or not 0 <= dest < len(entries):
            return False
        entries.insert(dest, entries.pop(index))
        return self.setValue("corners", corner, entries)

    @Slot(str, int, result=bool)
    def removeCornerField(self, corner, index):
        if corner not in CORNERS:
            return False
        entries = list(self._data["corners"][corner])
        if not 0 <= index < len(entries):
            return False
        entries.pop(index)
        return self.setValue("corners", corner, entries)


def resolve_settings(parent):
    """Standalone controllers use isolated defaults; the app owns persistence."""
    ancestor = parent
    while ancestor is not None:
        settings = getattr(ancestor, "_settings_controller", None)
        if settings is not None:
            return settings
        ancestor = ancestor.parent()
    return SettingsController(parent, path=False)
