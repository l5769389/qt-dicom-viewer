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

## Windows 单文件 EXE

在 **Windows x64** 上安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)，
然后在项目根目录的 PowerShell 或 CMD 中运行：

```powershell
.\scripts\build_windows.bat
```

脚本会通过 uv 准备 Python 3.13、在独立的 `.venv-build-windows` 环境中安装
`uv.lock` 锁定的运行依赖和 PyInstaller，并生成：

```text
dist/DICOMVision.exe
```

只需复制这个 EXE 到目标 Windows 电脑即可启动，无需另装 Python、uv 或 Qt。
首次构建需要联网下载依赖；再次构建会复用下载缓存，并覆盖同名 EXE，请先退出正在运行的旧版本。
构建中间文件和自动生成的 spec 位于 `build/windows`，不会覆盖日常开发的 `.venv`。

### 在 Mac 上通过 GitHub Actions 打包

无需本地安装 Windows：工作流会在 GitHub 提供的 Windows x64 环境中执行测试和打包。

1. 将要打包的代码推送到仓库。
2. 打开仓库的 [Build Windows EXE](https://github.com/l5769389/qt-dicom-viewer/actions/workflows/build-windows.yml) 页面。
3. 点击 **Run workflow**，选择分支；需要诊断版本时勾选控制台选项。
4. 等待测试、打包和上传步骤全部成功。
5. 在该次运行页面的 **Artifacts** 中下载 `DICOMVision-windows-x64`，解压即可得到 EXE。
   诊断版对应 `DICOMVision-windows-x64-debug`。

工作流仅手动触发，不会在每次推送时自动构建。下载产物保留 14 天；需要长期保存时请自行下载归档。
私有仓库的查看和下载需要仓库访问权限，构建和产物存储会计入 GitHub Actions 对应额度。
工作流配置位于 `.github/workflows/build-windows.yml`，复用本地打包脚本与锁定依赖。

### 打包内容与限制

- 包含应用 Python 代码、QML、`qmldir`、图片、SVG、Qt 插件和运行依赖。
- 不包含本地 DICOM 数据；打包后的解码能力与项目依赖一致，不会自动增加 JPEG/JPEG-LS 等额外解码器。
- 默认不显示控制台。单文件模式启动时会解压到系统临时目录，因此启动比源码运行慢、EXE 也较大。
- 必须在 Windows 上构建；当前脚本不支持从 macOS/Linux 交叉生成 EXE，详见
  [PyInstaller 平台说明](https://pyinstaller.org/en/stable/operating-mode.html)。
- EXE 尚未进行代码签名，Windows 可能提示来源未知；公开分发前需自行安排签名和目标机验证。

### 启动问题排查

生成保留控制台的诊断版本（不会覆盖普通版本）：

```powershell
.\scripts\build_windows.bat --console
.\dist\DICOMVision-debug.exe
```

应用日志保存在 Qt `AppLocalDataLocation` 对应目录下的 `logs/dicomvision.log`。
在 Windows 上通常是 `%LOCALAPPDATA%\QtDicomViewer\Qt DICOM Viewer\logs\dicomvision.log`。
普通 EXE 同样保留文件日志；QML 插件加载问题优先查看诊断版本的控制台输出。

打包后请在没有安装 Python/Qt 的 Windows x64 电脑上验证：启动界面、打开 DICOM、
2D 翻页/调窗、MPR 旋转、测量以及正常退出。打包成功本身不代表这些功能已经通过目标机验收。

## Suggested Drills

1. Change text, colors, and spacing in `Main.qml`.
2. Add another `Rectangle` panel.
3. Add a `Button` that calls a Python `@Slot`.
4. Add a new Python `@Property` and bind it in QML.
5. Add a `ListView` with a Python-provided list model.
