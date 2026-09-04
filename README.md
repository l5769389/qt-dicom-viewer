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

## 4D MPR

选择包含多个时间相位的 series 后，可通过左侧「4D」打开三视图 MPR。右侧控制区支持
右侧「播放」工具的二级面板支持 1～15 FPS 循环播放、phase 滑块和编号选择；默认显示
第一个 phase，播放速度为 2 FPS。
切换 phase 会保留十字线、当前空间位置、调窗、平移、缩放、旋转和测量状态，滚轮仍用于
当前 phase 内的 MPR 空间翻页。

4D 数据按“一个经典单帧 Series 对应一个 phase、多个 Series 组成一个 4D 组”进行关联。
当前支持常见的时间/心动/呼吸 phase 信息，包括
`TemporalPositionIdentifier`、`TemporalPositionIndex`、`PhaseNumber`、phase 百分比、
trigger/delay、`FrameReferenceTime`、`AcquisitionNumber` 以及采集/内容时间等字段。
检测按明确 phase 标签优先；采集编号和时间只作为后备，并且必须在每个值下形成至少两层、
层数与空间位置完全对应的体数据。`NumberOfTemporalPositions` / `NumberOfPhases` 存在时还会
校验总数，以避免把普通逐层采集误判为 4D。对于缺少标准时间标签的派生数据，也支持从
`SeriesDescription` 末尾的 `phN` / `phaseN` 提取 phase；此方式仍要求 Study、Frame of
Reference、模态和整套空间几何一致。Enhanced Multi-frame DICOM 仍不支持；不符合条件的
series 不会启用「4D」入口。

## 测量

在右侧「测量」中选择长度、角度、矩形或椭圆，测量可绘制到整个视口画布，
不限于影像矩形内部。

- **长度 / 矩形 / 椭圆**：按住左键拖动，松开完成。
- **角度**：依次点击起点、顶点、终点；也可先拖出第一条边，松开确定顶点，
  再拖出第二条边并松开完成。两段之间移动鼠标可预览第二条边。
- **编辑**：点击轮廓、标签或 ROI 内部选中；拖动控制点调整形状，拖动轮廓、标签、
  metric 信息块或 ROI 内部整体移动图形。选中图形的可移动部位悬停时显示四向移动图标，
  控制点不会显示整体移动图标。椭圆的四个控制点位于其包围盒角点上。
- **取消 / 删除**：视口获得焦点后，`Esc` 取消当前绘制或恢复编辑前的结果，
  `Delete` / `Backspace` 删除选中测量。「重置测量」清除当前视口的所有测量。

矩形和椭圆旁显示独立信息块：几何面积（mm²）、宽高 / 轴径（mm）、均值、标准差、
最小 / 最大值和有效像素数。文字、控制点大小与线宽保持屏幕尺寸，影像缩放、旋转、
镜像不会让信息块文字跟着变形。

计算约定：

- 长度、角度和面积使用当前图像的行 / 列物理间距；角度第二点为顶点，范围为 0～180°。
- ROI 统计使用原始模态像素（MPR 中使用重采样后的模态像素），不使用调窗后的显示灰度；
  CT 数值标注 HU。移动 ROI 后统计会重新计算。
- 以**像素中心位于轮廓内**判定是否纳入统计；椭圆使用椭圆掩膜，而不是整个包围盒。
  标准差采用总体标准差（`ddof=0`），NaN / Inf 及图像范围外的位置不计入统计。
- 面积是完整轮廓的几何面积，不是有效像素数乘以像素面积。完全位于影像外的 ROI
  仍显示尺寸与面积，但灰度统计显示「—」，不会伪造为 0。
- 测量按切片及采样网格隔离；MPR 原点、方向或间距改变后，不将旧轮廓套在新网格上。
  回到相同网格可恢复显示。当前测量仅保存在本次会话内，尚不导出为 DICOM SR。

### 命中判断结构

`MeasurementController.hit_test()` 负责当前切面筛选和优先级，具体几何判断在
`core/measurement_hit_test.py` 中独立实现。命中结果的 `measurement_id` 表示所属图形，
`target.kind` 表示部位，`target.index` 表示该部位的编号：

| 部位 | 含义 | index |
| --- | --- | --- |
| `CONTROL_POINT` | 可调整形状的控制点 | 起点 / 顶点 / 终点或包围盒角点的编号 |
| `OUTLINE` | 长度线段、角度两条边、矩形 / 椭圆轮廓 | 直线边编号；椭圆为 `None` |
| `INTERIOR` | 矩形 / 椭圆内部，不包含边界 | `None` |
| `LABEL` | 长度 / 角度文字或 ROI metric 信息块 | `None` |

测量内部的命中优先级为：控制点 > 标签 > 轮廓 > ROI 内部。
内部命中与是否选中无关，未选中 ROI 也可以通过点击内部选中；选择状态只参与重叠优先级和光标提示。
同类几何命中选距离最近的；同距离优先选中项，再优先后绘制项。标签重叠时按相同的叠放顺序选择。
十字线操作仍由视口原有逻辑优先处理，不混入这些测量部位。

控制点、轮廓和内部使用图像坐标；标签使用 QML 实际布局提供的视口矩形，避免缩放、
旋转、镜像后命中位置偏离。部位与动作分开：`OUTLINE`、`INTERIOR`、`LABEL` 当前都执行
整体平移，但不会丢失命中的具体部位。QML 的 `activeTransaction.editTarget` 也会提供 `kind` / `index`。
`measurementController.hoverHit` 提供悬停命中的 `measurementId` / `kind` / `index`；
`hoverCursorKind` 只在已选中图形的可移动部位返回 `pan`。离开、开始编辑、切换工具或切面时清除悬停状态。

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

## 服务菜单（预留入口）

“服务”仅在 2D 视图的右侧一级工具栏中显示和启用，MPR、3D、4D、Tag 视图不提供此工具。
内容区仅显示 MTF、QA 两个 PNG 图片按钮，靠顶部排列，不显示标题或预留说明。
当前仅支持入口选择，不会开启矩形绘制、MTF 计算或 QA 检查。
从测量切换到服务时会退出绘制模式；切回测量可继续正常使用原有工具。
服务没有独立的可重置内容，底部重置按钮禁用，顶部“全部重置”仍可使用。

图标位于 `src/qt_dicom_viewer/qml/assets/icons/`；MTF 当前采用深色底图片，服务与 QA 图片带透明通道。
生成方式与提示词记录在该目录的 `README.md` 中。

## Suggested Drills

1. Change text, colors, and spacing in `Main.qml`.
2. Add another `Rectangle` panel.
3. Add a `Button` that calls a Python `@Slot`.
4. Add a new Python `@Property` and bind it in QML.
5. Add a `ListView` with a Python-provided list model.
