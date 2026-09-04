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

## 服务菜单与微珠法 MTF

“服务”仅在 2D 视图的右侧一级工具栏中显示和启用，MPR、3D、4D、Tag 视图不提供此工具。
内容区顶部 MTF、QA 两个 PNG 图片按钮等宽并排，不显示“服务”标题或预留说明。QA 仅保留入口。
X/Y 及圆点 MTF50、菱形 MTF10 图例位于图表右上角；点击 X 或 Y 可独立隐藏对应曲线和标记。

在原始 2D 切片选择“服务 → MTF”，框选**单颗微珠及外围背景**。矩形至少包含 8 × 8 个像素，
必须完全位于原始图像内。每切片、每采样几何保留一个 ROI；成功提交新框替换旧框，取消则保留旧框。
8 × 8 只是输入下限，不是推荐值，也不应把固定像素数用于不同 PixelSpacing。可先使用约 4 × 4 mm
的方形 ROI，再在约 3～5 mm 范围内调整并检查结果是否稳定。ROI 应完整覆盖亮峰及周围欠冲，外围带
需要能够代表背景，同时避开邻近结构。参考研究使用约 0.098 mm 像素，30～50 像素才对应约
2.9～4.9 mm；其微珠法最优值随重建核为 38、40 或 50 像素，并不存在通用的 40 像素规则。
MTF ROI 在新建和角点缩放时固定为物理尺寸上的正方形；行列 PixelSpacing 不同时，像素宽高可以不同。
支持四角缩放、轮廓或内部整体移动、Esc 取消、Delete / Backspace 删除；小框按短边自适应缩小角点和边线命中范围。
MTF 轮廓旁优先显示 ROI 的 X/Y 物理尺寸，随后显示像素数及 X/Y 的 MTF50 与 MTF10，不显示普通 ROI 统计卡；
普通测量与 MTF 的选择、编辑及数据互相隔离。
翻页取消草稿，返回原切片恢复已提交的框及结果；退出 MTF 工具保留轮廓但不能编辑。

默认采用“微珠 + 直接 FFT”。右侧可切换“微珠 / 细丝”和“直接 FFT / 高斯拟合”：
切换测试体会清除当前视口全部 MTF ROI 与结果；切换分析方式保留当前 ROI 并立即重新计算。
细丝模式当前指垂直于扫描平面的细丝截面，它与微珠一样作为二维点源响应分析，不支持画面内任意方向的长细丝。

松开提交后，Qt 线程池分析 ROI 的原始模态像素快照。拖动只更新几何；调窗、平移、缩放、镜像、
显示旋转和悬停均不重算 MTF。旧任务不能覆盖新版 ROI，删除、重置、关闭后返回的结果被忽略。
编辑时隐藏旧曲线，取消恢复结果；当前 ROI 计算失败时显示错误，不展示旧数值。
“重置 MTF”清除当前视口所有切片的 MTF ROI / 结果；QA 下底部重置禁用。
“重置测量”不影响 MTF，“全部重置”同时清除两类数据。

右侧 Canvas 展示 X（原始列方向，实线）/ Y（原始行方向，虚线）曲线和指标：

- MTF50、MTF10：单位 lp/mm，取零频起第一次向下穿越阈值的线性插值交点；无交点显示“未达到”。
- FWHM：单位 mm。直接 FFT 模式测量扣背景 LSF 主峰左右最近的半峰高交点；高斯模式报告拟合曲线的
  `2√(2ln2)σ`。任一侧无交点时显示“无法测量”。X/Y 不随显示旋转交换。
- ROI 外围带宽为短边的 10% 向上取整，至少一个像素；背景采用外围带中位数。
  PSF 保留负值，各列/行积分并乘正交方向间距获得 LSF。
- LSF 补零至至少四倍长度的下一个二次幂，取 rFFT 幅值并按零频归一化；保留响应大于 1 的部分。
  两方向按真实 DICOM PixelSpacing 分别限定 Nyquist 频率，不使用显示层 1 mm 回退值。
- 平坦、无有效正净响应、越界、非法间距或非有限像素显示明确错误。
  外围 MAD 噪声、主峰位置、LSF 两端和多次阈值穿越仅用于质量提示，不作自动合格判定。

直接 FFT 不加窗、不平滑、不取 PSF 绝对值；高斯模式对方向 LSF 拟合带常数基线的一维高斯，
显示解析高斯 MTF 及等效 MTF50 / MTF10 / FWHM，并在拟合度较低时警告。
两种测试体均未做有限尺寸修正，也不做跨切片平均、导出或 MPR 分析。
界面不再重复显示微珠尺寸修正提示；这只是显示调整，不代表算法已启用尺寸修正。
合成高斯解析基准验证不等同于真实模体重复性验证；目前不宣称达到临床质控精度。
方法参考：[Catphan 700 手册](https://www.phantomlab.com/s/Catphan700Manual.pdf)、
[PhantomLab 方向 MTF 说明](https://help-smari.phantomlab.com/hc/en-us/articles/4402017982355-Modulation-Transfer-Function-MTF)。

实现入口：`core/bead_mtf.py`（纯 NumPy）、`model/mtf.py`（结果类型）、
`ui/controller/viewport/controller/mtf_controller.py`（ROI / 异步缓存）。
`tests/test_bead_mtf.py`、`tests/test_mtf_controller.py`、`tests/test_mtf_qml.py` 分别覆盖数学、状态与真实 QML 操作。

### 与参考软件比对 MTF50 / MTF10

先确认同一原始切片、同一颗微珠、同一 ROI，以及单位（lp/mm 或 lp/cm）和方向定义（X/Y 或径向平均）。
直接 FFT 模式取方向 LSF 的傅里叶幅值，以零频归一化，不做峰值归一化、拟合或平滑。
频率数组使用原始 DICOM PixelSpacing；显示缩放、旋转和窗口不改变分析像素或物理间距。

通过解析高斯及离散三点响应核检查了 0.7、1.13 lp/mm 量级的 MTF50、MTF10：
未发现固定频率倍率或阈值互换。**这不能证明某个真实 ROI 的结果正确**。
外围带必须确实代表背景；小框把微珠尾部当作背景，会造成扣除过量、LSF 变窄和 MTF 偏高。
合成对照：理论 MTF50=0.7、间距 0.06 mm 的同一高斯微珠，64×64 框得到约 0.700/1.277（MTF50/10），
中心 16×16 框得到约 1.128/1.733，估计背景从真值 80 升至约 288。
这只是可复现的偏差机制，不是尚未取得的真实 DICOM 的诊断。
可围绕同一微珠适度扩大 ROI，检查曲线与阈值是否趋于稳定，同时避开邻近结构；不是框越大越好。
间距错误更像两项频率同时按相同比例偏移；背景或处理流程不同则可能改变整条曲线的形状。
ROI 依赖性也见[微珠 / 丝法 ROI 尺寸研究](https://pubmed.ncbi.nlm.nih.gov/23835372/)。

图标位于 `src/qt_dicom_viewer/qml/assets/icons/`；MTF 当前采用深色底图片，服务与 QA 图片带透明通道。
生成方式与提示词记录在该目录的 `README.md` 中。

## Suggested Drills

1. Change text, colors, and spacing in `Main.qml`.
2. Add another `Rectangle` panel.
3. Add a `Button` that calls a Python `@Slot`.
4. Add a new Python `@Property` and bind it in QML.
5. Add a `ListView` with a Python-provided list model.
