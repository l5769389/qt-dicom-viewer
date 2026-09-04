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

## 3D 体绘制

打开 DICOM 文件夹，选择序列后点击左侧 **3D**。首次加载在后台构建体数据，
默认从患者前方观看（A 面朝向用户、头侧朝上），使用通用模板和序列默认窗宽窗位。

- **旋转**：默认工具，按住左键拖动。
- **平移 / 缩放**：选择右侧对应工具后按住左键拖动；缩放向上拖动放大。
- **滚轮 / 触控板滚动**：始终用于缩放。
- **交互画质**：旋转、平移、缩放和调窗期间使用与松手后相同的体射线采样步长，
  不会因拖动临时降低画质；连续指针事件按一帧合并，避免重复绘制拖慢操作。
- **方向**：一级按钮显示当前最朝向用户的一个字母，点击后在右侧选择前 A、后 P、左 L、右 R、上 S、下 I。
  自由旋转时字母与面板选中项实时联动；斜视也只选一个方向。切换方向保留平移、缩放和模板。
- **模板**：右侧按 General / CT / CTA 分组提供通用、MIP、XRay、骨骼、肺、血管。
  骨骼、肺、血管仅在 CT 序列中启用。切换或再次点击模板会载入其默认窗，保留视角。
- **调窗**：选中后按住左键拖动，向右增大窗宽、向上提高窗位，颜色和透明度范围一起调整。
  仅支持拖动，没有窗预设列表或数值输入；窗宽最低为 1，不会反相。
- **重置**：底部按钮只重置当前工具；调窗回到当前模板默认值，模板回到通用，旋转/方向回到 A 正面。
  顶部全部重置恢复初始视角、位置、比例和通用模板的序列默认窗。
- **方向 Cube**：右上角显示 L/R（左/右）、A/P（前/后）、S/I（上/下），
  六面分别为 A 绿、P 青、L 红、R 橙、S 蓝、I 紫，文字为白色。
  按患者 LPS 坐标随视角同步旋转；平移和缩放不会改变它的方向或屏幕尺寸。
  Cube 仅作方向提示，标准视角通过右侧方向面板选择。

不同序列的 3D Tab 独立保存视角、模板和窗值，切换到 2D/MPR 后再切回也会保留。
关闭 Tab 释放其原生视口和 VTK 渲染资源；原始体数据仍由现有 VolumeManager 缓存复用。

当前支持至少两张单帧切片组成的规则体数据，包括具有一致斜向方向的序列。
缺少空间位置/方向、重复位置、不等距切片、层间横向偏移或不一致矩阵的序列会显示错误，
不使用猜测的几何信息绘制。增强多帧 DICOM、非规则网格重采样和外部模板配置读取留待后续扩展。

模板目前使用内置数据，运行时不依赖小赛看看。配色参考及本项目的参数定义详见
[3D 模板参数与扩展约定](docs/volume-presets.md)。

### 集成结构

主窗口、Tab、左右工具栏、2D 和 MPR 界面继续使用 QML。
只有 3D Tab 内容区使用 `WindowContainer → QWidget → QVTKRenderWindowInteractor`，
直接调用 Python VTK 9.5.2；没有 C++ 桥接或 Qt Quick 3D 依赖。

`VolumeViewportController` 管理独立视角、显示状态和加载状态；`VolumeViewportHost` 管理原生窗口、
输入和渲染调度；`VolumeRenderBackend` 管理体绘制及方向 Cube。
后续裁剪、表面提取等功能可以扩展 VTK 后端和控制器。
原生内容由独立窗口合成；需要覆盖在体绘制上的后续控件应放在这个原生内容区，
不能依赖普通 QML Item 的层级遮盖它。切换 Tab 先隐藏、分离窗口，关闭时再释放。
体数据解码在线程中完成，VTK/OpenGL 对象和渲染始终留在 GUI 线程。

### 验证

```bash
uv run --group dev pytest -q
uv run python scripts/smoke_3d.py
```

第二条命令需要真实桌面会话和 OpenGL。它临时生成合成 DICOM 序列，验证后台加载、
QML 工具按钮、六面方向同步、六类模板、拖动调窗及重置、交互/静止帧画质一致性、窗口缩放、2D/3D 切换、多 Tab、关闭和重新打开，
完成后自动退出。可附加 PNG 路径导出 VTK 视口，例如 `scripts/smoke_3d.py /tmp/volume.png`。
普通 pytest 验证视角数学、斜向坐标映射、输入校验、异步结果隔离和现有功能回归，
不能替代目标系统的显卡、窗口合成及高 DPI 验证。

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

- 包含应用 Python 代码、QML、`qmldir`、图片、SVG、Qt 插件、VTK 渲染模块和运行依赖。
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
2D 翻页/调窗、MPR 旋转、测量、3D 体绘制/操作/方向 Cube/Tab 切换以及正常退出。
打包成功本身不代表这些功能已经通过目标机验收。

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
