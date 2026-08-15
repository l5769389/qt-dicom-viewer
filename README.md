# Qt DICOM Viewer

A lightweight DICOM viewer built with PySide6 and QML.

## Run

```bash
uv run qt-dicom-viewer
```

## Dev Auto-Restart

```bash
uv run --group dev watchfiles "uv run qt-dicom-viewer" src
```

When a Python file under `src` changes, the Qt app restarts automatically.

## Suggested Drills

1. Change text, colors, and spacing in `Main.qml`.
2. Add another `Rectangle` panel.
3. Add a `Button` that calls a Python `@Slot`.
4. Add a new Python `@Property` and bind it in QML.
5. Add a `ListView` with a Python-provided list model.
