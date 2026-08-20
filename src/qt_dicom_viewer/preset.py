from qt_dicom_viewer.model import WindowPreset

CT_WINDOW_PRESETS = (
    WindowPreset(
        preset_id="ct-brain",
        label="脑组织",
        center=40,
        width=80,
    ),
    WindowPreset(
        preset_id="ct-lung",
        label="肺窗",
        center=-600,
        width=1500,
    ),
    WindowPreset(
        preset_id="ct-bone",
        label="骨窗",
        center=300,
        width=1500,
    ),
    WindowPreset(
        preset_id="ct-soft-tissue",
        label="软组织",
        center=40,
        width=400,
    ),
)