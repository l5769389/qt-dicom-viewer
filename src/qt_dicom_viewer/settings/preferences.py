"""Validated JSON schema for user preferences (no image or patient data)."""
from copy import deepcopy
from math import isfinite
import re

from qt_dicom_viewer.core.color_maps import COLOR_MAPS
from qt_dicom_viewer.preset import CT_WINDOW_PRESETS

CORNER_FIELDS = {
    "viewPosition": "切面 / 位置", "manufacturer": "制造商", "seriesDescription": "序列描述",
    "studyDescription": "检查描述", "modality": "模态", "slice": "切片 / 总数",
    "patientName": "患者姓名", "patientId": "患者 ID", "exposure": "kV / mA",
    "sliceThickness": "层厚", "window": "窗宽 / 窗位", "cursor": "坐标 / 像素值",
    "zoom": "缩放", "transform": "旋转 / 镜像", "instanceNumber": "实例号",
    "matrix": "图像矩阵", "spacing": "像素间距", "seriesUid": "序列 UID",
}
CORNERS = ("topLeft", "topRight", "bottomLeft", "bottomRight")
METRICS = {"mean": "均值 Mean", "std": "标准差 StdDev", "minimum": "最小值 Min",
           "maximum": "最大值 Max", "area": "面积 Area", "width": "宽度 Width",
           "height": "高度 Height", "count": "有效像素数"}
DEFAULTS = {
    "colormap": {"gray": "grayscale", "pet": "grayscale"},
    "window": {"hidden": [], "custom": []},
    "crosshair": {"axialColor": "#ff0000", "coronalColor": "#008000", "sagittalColor": "#0000ff",
                  "axialWidth": 1.0, "coronalWidth": 1.0, "sagittalWidth": 1.0},
    "corners": {"enabled": True, "fontSize": 12, "lineHeight": 1.2,
                "colorMode": "auto", "color": "#f8fafc",
                "topLeft": ["viewPosition", "manufacturer", "seriesDescription", "slice"],
                "topRight": ["patientName", "patientId"],
                "bottomLeft": ["exposure", "sliceThickness", "window"], "bottomRight": ["cursor"]},
    "scale": {"enabled": True, "color": "#f8fafc"},
    "measurement": {"editingColor": "#66d0ff", "completedColor": "#ffd45c", "lineWidth": 1.5,
                    "editingDash": True, "completedDash": False, "fontSize": 13,
                    "annotationColor": "#ffd166", "annotationSize": 14},
    "roi": {key: True for key in METRICS},
}


def validate_value(section, key, value):
    if section not in DEFAULTS or key not in DEFAULTS[section]:
        raise ValueError("未知设置项")
    default = DEFAULTS[section][key]
    if isinstance(default, bool):
        if not isinstance(value, bool):
            raise ValueError("请选择启用或关闭")
    elif key.lower().endswith("color"):
        if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError("颜色格式应为 #RRGGBB")
        value = value.lower()
    elif section == "colormap":
        if value not in COLOR_MAPS:
            raise ValueError("请选择有效伪彩")
    elif key == "colorMode":
        if value not in ("auto", "custom"):
            raise ValueError("请选择有效颜色策略")
    elif isinstance(default, (int, float)):
        limits = {"fontSize": (10, 20), "lineHeight": (1, 1.8), "lineWidth": (1, 6), "annotationSize": (8, 28)}
        low, high = limits.get(key, (1, 6))
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value) or not low <= value <= high:
            raise ValueError(f"数值范围为 {low}–{high}")
        value = int(round(value)) if isinstance(default, int) else round(float(value), 2)
    elif section == "corners" and key in CORNERS:
        if not isinstance(value, list) or len(value) > 8 or any(v not in CORNER_FIELDS for v in value) or len(set(value)) != len(value):
            raise ValueError("每个角最多显示 8 项，且不能重复")
    elif section == "window" and key == "hidden":
        ids = {p.preset_id for p in CT_WINDOW_PRESETS}
        if not isinstance(value, list) or any(v not in ids for v in value):
            raise ValueError("无效的系统窗模板")
        value = list(dict.fromkeys(value))
    elif section == "window" and key == "custom":
        if not isinstance(value, list) or len(value) > 20:
            raise ValueError("最多保存 20 个自定义窗模板")
        ids, labels, validated = set(), set(), []
        for item in value:
            if not isinstance(item, dict):
                raise ValueError("窗模板格式错误")
            name, identifier = str(item.get("label", "")).strip(), str(item.get("presetId", ""))
            if not name or len(name) > 40 or name.casefold() in labels or not re.fullmatch(r"custom-[a-zA-Z0-9-]+", identifier) or identifier in ids:
                raise ValueError("模板名称不能为空或重复，最多 40 字")
            width, center = item.get("width"), item.get("center")
            if any(isinstance(v, bool) or not isinstance(v, (float, int)) or not isfinite(v) for v in (width, center)) or not 1 <= width <= 1000000 or not -1000000 <= center <= 1000000:
                raise ValueError("窗宽应为 1–1000000，窗位应为 -1000000–1000000")
            ids.add(identifier)
            labels.add(name.casefold())
            validated.append(dict(presetId=identifier, label=name, width=float(width), center=float(center), enabled=bool(item.get("enabled", True))))
        value = validated
    return deepcopy(value)


def normalize_settings(raw):
    data = deepcopy(DEFAULTS)
    if not isinstance(raw, dict):
        return data
    for section, entries in data.items():
        candidate = raw.get(section, {})
        if not isinstance(candidate, dict):
            continue
        for key in entries:
            if key in candidate:
                try:
                    entries[key] = validate_value(section, key, candidate[key])
                except (ValueError, TypeError):
                    pass
    return data
