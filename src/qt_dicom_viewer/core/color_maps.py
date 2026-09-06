"""Display-only LUTs shared by the renderer and settings previews."""
from functools import lru_cache

import numpy as np

# Equally spaced control points; UI previews use these same values.
COLOR_MAPS = {
    "grayscale": ("BW", ("#000000", "#ffffff")),
    "bwInverse": ("BW Inverse", ("#ffffff", "#000000")),
    "blackBody": ("Black Body", ("#000000", "#a00000", "#ff4200", "#ffe500", "#ffffff")),
    "hotIron": ("Hot Iron", ("#000000", "#800000", "#ff2300", "#ffad40", "#ffffff")),
    "hotMetal": ("Hot Metal", ("#000000", "#790000", "#c22a00", "#e8be20", "#ffffdf")),
    "pet": ("PET", ("#000000", "#007b7b", "#5900c8", "#e77e21", "#ffffff")),
    "rainbow": ("Rainbow", ("#24004f", "#073fc4", "#04975e", "#75bb00", "#f9c324", "#e63220")),
}


@lru_cache(maxsize=7)
def color_lut(name: str) -> np.ndarray:
    colors = COLOR_MAPS[name][1]
    rgb = np.array([[int(c[i:i + 2], 16) for i in (1, 3, 5)] for c in colors])
    x = np.linspace(0, 255, len(colors))
    lut = np.stack([np.interp(np.arange(256), x, rgb[:, c]) for c in range(3)], axis=1)
    result = np.rint(lut).astype(np.uint8)
    result.flags.writeable = False
    return result


def apply_color_map(pixels: np.ndarray | None, name: str) -> np.ndarray | None:
    if pixels is None or pixels.ndim != 2 or name == "grayscale":
        return pixels
    return np.ascontiguousarray(color_lut(name)[pixels])
