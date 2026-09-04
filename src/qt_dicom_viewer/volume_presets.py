"""Built-in display presets. A future file loader can supply the same data types.

Bone/vessel RGB anchors are sampled from XiaoSaiViewer 2.6.2's readable CLUTs;
bone/lung windows reference its WLWW.xml. Opacity, lighting and vessel window
are project defaults, not a reconstruction of its binary vrConifg.xml.
See docs/volume-presets.md for provenance and parameter conventions.
"""
from types import MappingProxyType

from qt_dicom_viewer.model.dicom_types import WindowLevel
from qt_dicom_viewer.model.volume_models import VolumeBlendMode, VolumePreset


def _rgb_anchors(samples):
    return tuple((index/255, r/255, g/255, b/255) for index, r, g, b in samples)


GRAYSCALE = ((0.0, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0))
BONE_COLORS = _rgb_anchors((
    (0, 0, 0, 0), (32, 56, 39, 9), (64, 112, 78, 18),
    (96, 169, 118, 27), (128, 219, 154, 36), (160, 235, 175, 43),
    (192, 251, 196, 50), (224, 255, 228, 60), (255, 255, 254, 237),
))
VESSEL_COLORS = _rgb_anchors((
    (0, 0, 0, 0), (32, 41, 0, 0), (64, 82, 0, 0),
    (96, 123, 0, 0), (128, 165, 0, 0), (160, 204, 11, 7),
    (192, 239, 65, 39), (224, 255, 126, 92), (255, 255, 248, 247),
))

VOLUME_PRESETS = (
    VolumePreset("general", "通用", "General", GRAYSCALE,
                 tuple((i/16, 0.08*(i/16)**2) for i in range(17))),
    VolumePreset("mip", "MIP", "General", GRAYSCALE, ((0, 0), (1, 1)),
                 blend_mode=VolumeBlendMode.MIP, shade=False),
    VolumePreset("xray", "XRay", "General", GRAYSCALE, ((0, 0), (1, 1)),
                 blend_mode=VolumeBlendMode.ADDITIVE, shade=False),
    VolumePreset("bone", "骨骼", "CT", BONE_COLORS,
                 ((0, 0), (0.35, 0), (0.45, 0.04), (0.6, 0.25), (1, 0.8)),
                 default_window=WindowLevel(center=300, width=1500), ct_only=True),
    VolumePreset("lung", "肺", "CT", GRAYSCALE,
                 ((0, 0), (0.15, 0), (0.2, 0.05), (0.4, 0.12), (0.65, 0.04), (0.8, 0), (1, 0)),
                 default_window=WindowLevel(center=-400, width=1500), ct_only=True),
    VolumePreset("vessel", "血管", "CTA", VESSEL_COLORS,
                 ((0, 0), (0.1, 0), (0.2, 0.05), (0.5, 0.25), (1, 0.8)),
                 default_window=WindowLevel(center=400, width=700), ct_only=True),
)
VOLUME_PRESET_BY_ID = MappingProxyType({preset.preset_id: preset for preset in VOLUME_PRESETS})
