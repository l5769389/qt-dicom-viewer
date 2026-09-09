# 序列侧栏与影像工具优化验证

- 日期：2026-09-08
- 基线：本地 `main`，`651c187`。
- 分支：`codex/series-tools-polish`。
- 环境：macOS，Qt offscreen / software backend。未运行 Windows 原生界面验证。

## 覆盖范围

- 大量合成序列的虚拟化滚动、缩略图增量更新、结构变化后的可见行锚定、搜索回到顶部，以及小窗口下固定的顶部和底部。无结构变化时位置误差断言不超过 1 像素。
- 跨患者与搜索隐藏项的批量移除、右键保留勾选、清空、扫描期间禁用、迟到结果过滤及清空后重新导入；移除后源文件和已打开视图仍保留。
- CT 窗宽／窗位按钮及回车提交、无效输入、模板保存、名称重复校验、持久化恢复和删除；MPR／4D 三方向共享窗值、反色、重置、旧结果过滤及时相切换。
- 两种箭头标注模式的控件显隐与删除、水模 QA 手册入口和返回后结果保留，以及文字导出按钮的现有流程。
- 真实 QML 窄面板布局检查和控制器回归。

## 测试结果

首轮完整测试集排除以下已知基线崩溃后：**887 passed, 15 skipped, 1 deselected**，耗时 161.91 秒。

```sh
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software PYTHONPATH=src:tests \
  /Users/jun/Documents/git-repo/qt-dicom-viewer/.venv/bin/python -m pytest -q --tb=short \
  --deselect=tests/test_worktree_integration.py::test_image_and_volume_tab_transitions_keep_controller_types_separate \
  --basetemp=/private/tmp/series-polish-handoff-validation
```

15 项跳过为需要显式启用的 Docker / PACS 测试。587 条警告来自 VTK / NumPy 弃用提示与合成 DICOM 私有标签的 VR 提示。

最终测试输出：`/private/tmp/series-polish-handoff-pytest.log`（临时文件）。

## 首轮基线问题（本轮已通过该项回归）

`tests/test_worktree_integration.py::test_image_and_volume_tab_transitions_keep_controller_types_separate` 在关闭 3D 页签后再次创建 3D 页签时发生原生段错误（退出码 139），调用栈涉及 `WorkspaceController.activateTabId` 和 Qt QML 的 `QObjectWrapper::getProperty`。

该崩溃已在未修改的原始 `main` 工作目录单独运行 `tests/test_worktree_integration.py` 时复现，同样发生于测试第 126 行的 3D 重开步骤。首轮未修改这项测试，也未将该项计入首轮通过结果。下方记录的新加载流程已重新纳入并通过这项测试。


## 标注、服务图标与窗模板样式补充验证

2026-09-08 根据界面反馈补充：两种标注模式均提供线宽和箭头大小滑块；色板在 220 px 侧栏中保持单行、等大；纯箭头颜色入口接入实际显示样式。服务扳手图标重新绘制并统一为 24 px。窗值应用／模板保存使用主按钮，保存为模板使用描边按钮，取消使用文字按钮；模板行固定 36 px，文字与自定义模板删除按钮垂直居中。

受影响回归：**57 passed**，包括真实 QML 控件操作、220／250／330 px 模板布局、窄侧栏标注布局、图标状态渲染、设置、融合 CT 和服务面板。两条警告为已有的 VTK / NumPy 弃用提示，无 QML 绑定或布局警告。

```sh
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software PYTHONPATH=src:tests \
  /Users/jun/Documents/git-repo/qt-dicom-viewer/.venv/bin/python -m pytest -q \
  tests/test_ui_polish.py tests/test_series_tools_polish.py tests/test_app_icon_qml.py \
  tests/test_display_tools_qml.py tests/test_settings_redesign.py \
  tests/test_pet_workspace_qml.py tests/test_service_panel_qml.py
```

已查看真实 QML 截图，确认模板行和删除图标居中、按钮层次及服务图标尺寸。该轮仅运行受影响回归，未重复运行首轮完整测试集。


## 各视图工具顺序、独立 PET MPR 与统一加载

2026-09-08 完成各视图统一排序、独立 PET MPR 三视图、QML 异步页签创建、首轮影像／标签加载状态、取消打开、失败重试和迟到结果隔离。手册阅读位置在布局稳定后恢复；3D 原生视图延后到体数据就绪时创建。详细排列见 `docs/view-opening-and-tools.md`。

新增 21 项验收覆盖 CT／PET 2D、CT／PET MPR、平铺、3D、4D 和融合的加载状态，Tag 加载失败重试，关闭重开与迟到结果，以及慢后台任务期间 GUI 定时器和页签操作仍可响应。实际截图已检查 PET 三视图和 1000×600 窗口下的加载／错误界面。

最终重新运行完整测试集，**914 passed, 15 skipped**，耗时 172.67 秒，**没有 deselect**。15 项跳过仍为显式启用的 Docker / PACS 集成测试。587 条警告仍为 VTK / NumPy 弃用提示和合成 DICOM 私有标签提示。

```sh
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software PYTHONPATH=src:tests \
  /Users/jun/Documents/git-repo/qt-dicom-viewer/.venv/bin/python -m pytest -q --tb=short \
  --basetemp=/private/tmp/view-opening-complete
```

先前排除的 `test_image_and_volume_tab_transitions_keep_controller_types_separate` 在本轮先单独通过，随后也在完整测试集中通过。该测试结果不替代 Windows 实机验证或所有 GPU 驱动上的原生 VTK 验证。

最终测试日志：`/private/tmp/view-opening-complete.log`（临时文件）。本轮主分支和原工作目录中的未跟踪验证资料保持不变。


## 侧栏拖拽、独立 PET 3D、刻度尺与四角信息

2026-09-08 在同一 worktree 完成：左栏收起后的 28 px 展开栏；右侧工具栏 220–420 px、设置导航 156–300 px 拖拽与重启记忆；独立 PET 三维显示、真实单位转换、裁剪、PNG 导出、加载与失败重试；刻度尺屏幕长度上限；小视图字号与逐行省略。四角文本按行数复用，游标更新不重复创建同数量的文本控件。原工作目录及 main 保持不变，修改尚未提交。

新增 `tests/test_standalone_pet_volume.py`、`tests/test_resizable_view_layout.py`，离屏覆盖 17 项，包括单位转换保留相机与裁剪、无效数值、缺失单位、关闭与过期结果、真实裁剪任务、GPU 遮罩及物理坐标、宽度持久化和缩窗恢复、长中英文逐行截断、不同像素间距的刻度尺限长。更新旧测试的零宽收起栏、整块文本截断和尽量铺满刻度尺断言，以匹配新行为。

受影响回归最终 **43 passed, 3 skipped**；完整 pytest 最终 **931 passed, 18 skipped, 589 warnings**，耗时 183.78 秒，没有排除项。18 项跳过包含 15 项显式启用的 Docker/PACS 集成测试，以及以下另行执行的 3 项原生窗口测试。警告为 VTK/NumPy 弃用及合成 DICOM 私有标签提示，真实 QML 测试未发现布局或绑定警告。

```sh
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software PYTHONPATH=src:tests \
  /Users/jun/Documents/git-repo/qt-dicom-viewer/.venv/bin/python -m pytest -q \
  --basetemp=/private/tmp/pet3d-complete
```

macOS Cocoa 原生窗口另行验收 **3 passed**，覆盖 CT、独立 PET、融合 3D：展开按钮位于原生窗口之外且可点击，展开恢复宽度，右栏拖拽有效，PNG 包含真实三维影像。PET 额外验证裁剪改变导出像素、单位切换后遮罩与视角保留、整体重置恢复初始单位并清除裁剪。

```sh
VOXENRA_NATIVE_QA=1 QT_QPA_PLATFORM=cocoa QT_QUICK_BACKEND=software PYTHONPATH=src:tests \
  /Users/jun/Documents/git-repo/qt-dicom-viewer/.venv/bin/python -m pytest \
  tests/test_resizable_view_layout.py -k native_volume -q \
  --basetemp=/private/tmp/pet3d-native-final
```

已查看真实 PET PNG 和小窗口 MPR 截图。QQuickWindow 的截图不包含独立原生 VTK 子窗口，不能用其中央空白判定体绘制失败；三维图像另用原生导出截图验证。日志及截图为本机临时验证产物：

- 完整回归：`/private/tmp/pet3d-complete.log`
- 受影响回归：`/private/tmp/pet3d-target-final.log`
- 原生窗口回归：`/private/tmp/pet3d-native-final.log`
- PET 原生导出：`/private/tmp/pet3d-native-final/test_native_volume_sidebar_dra1/pet-3d.png`
- PET 裁剪并换单位导出：`/private/tmp/pet3d-native-final/test_native_volume_sidebar_dra1/pet-cropped-unit.png`
- 小窗口 MPR：`/private/tmp/pet3d-targeted/test_pet_panel_and_narrow_corn0/pet-mpr-compact.png`

当前环境没有 Windows 桌面，Windows 原生窗口的遮挡、拖拽和 GPU 驱动兼容性尚待实机验收。macOS 和离屏结果不能替代这项检查。


## 顶部统一品牌与零占位折叠（2026-09-09）

本轮取代上一轮 28 px 折叠栏：左侧完全隐藏，展开按钮放在顶部，与原生 VTK 窗口没有重叠。logo 和 Voxenra 名称集中显示在与主界面同色的顶部栏，移除左侧重复品牌。文件/PACS 按钮不再显示选中下划线。顶部提供窗口拖动、双击最大化、最小化/最大化/关闭和边缘缩放入口；macOS 使用左侧圆形按钮，其余平台使用右侧窗口按钮。小窗口设置导航使用更紧凑的行高和分组间距，保证底部分类可见。

应用组织名、应用名、默认导出目录、日志、bundle ID 与 Windows AppUserModelID 统一为 Voxenra（标识为 `com.junliu.voxenra`）；Qt 工程与资源文件为 `Voxenra.qmlproject`、`Voxenra.qrc`。旧名称仅保留在配置迁移、旧版安装清理和历史构建记录中。迁移复制旧窗模板/显示配置/PACS 配置，不覆盖已有新配置，不移动或删除影像及旧配置。内部 Python 包和兼容命令行入口保持兼容。

完整回归：**934 passed, 19 skipped, 589 warnings**，耗时 168.27 秒，无排除项。19 项跳过包括 15 项显式启用的 Docker/PACS 测试及 4 项原生桌面测试。原生 macOS Cocoa 单独执行 **4 passed**，覆盖 CT/PET/融合 3D 零占位折叠与恢复、工具栏拖拽、三维 PNG，以及窗口最小化、最大化、还原和关闭。最终提示文本与提示框颜色修正后，追加回归 **14 passed, 1 skipped**。真实 QML 检查未发现布局或绑定警告；589 条警告仍为既有 VTK/NumPy 弃用和合成 DICOM 私有标签提示。

```sh
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software PYTHONPATH=src:tests \
  /Users/jun/Documents/git-repo/qt-dicom-viewer/.venv/bin/python -m pytest -q \
  --basetemp=/private/tmp/voxenra-complete

VOXENRA_NATIVE_QA=1 QT_QPA_PLATFORM=cocoa QT_QUICK_BACKEND=software PYTHONPATH=src:tests \
  /Users/jun/Documents/git-repo/qt-dicom-viewer/.venv/bin/python -m pytest \
  tests/test_resizable_view_layout.py tests/test_window_chrome.py -k native -q
```

验证产物：

- 完整回归：`/private/tmp/voxenra-complete.log`
- 原生窗口：`/private/tmp/voxenra-native-verified.log`
- 最终顶部栏回归：`/private/tmp/voxenra-titlebar-final.log`
- 展开状态截图：`/private/tmp/voxenra-titlebar-final/test_title_brand_replaces_side0/voxenra-titlebar.png`
- 完全收起截图：`/private/tmp/voxenra-titlebar-final/test_title_brand_replaces_side0/voxenra-collapsed.png`

本轮桌面自动化连接超时，未完成通过真实系统鼠标事件验证标题栏拖动及窗口边缘缩放；对应 Qt 原生接口已接入。Windows 窗口和打包后的系统集成仍待实机验收。修改尚未提交，main 与原目录验证资料未改动。

## 紧凑缩略图栏与 32 px 顶部栏（2026-09-09）

本轮取代前一阶段“完全隐藏 / 顶部展开按钮”的布局。顶部栏由 44 px 压缩为 32 px，logo 为 20 px，名称字号为 13 px。左侧收起为 52 px 窄栏，显示 40 px 缩略图和固定底部展开按钮，展开恢复此前宽度。窄栏顶部保留文件夹入口（关闭本地数据源时使用 PACS 入口），空列表仍可导入和展开。

两种侧栏共用序列右键菜单和选择控制器，支持单击选择、Ctrl／⌘ 多选、双击打开 2D、右键打开各类视图、单项移除及批量删除。右键保留已有勾选，其他单项操作使用右键目标；源文件和已打开页签保持可用。3D 右键菜单使用独立 Qt 弹出窗口，避免被原生 VTK 子窗口遮挡。

紧凑列表使用独立的稳定行模型，沿用搜索范围，但显示折叠分组内部的序列。展开列表和紧凑列表各自保留滚动位置；缩略图结果只通知对应行变更，结构调整使用行 key 与偏移恢复位置。常规无分组折叠时复用已构建的行数据。

针对性真实 QML 回归：**35 passed, 4 skipped**。覆盖 140 个合成序列、连续缩略图结果、结构插入、搜索、折叠恢复、宽度恢复、右键跨搜索隐藏项批量删除以及双击打开视图；未变结构时可见行位置误差不超过 1 px。无 QML 布局或绑定警告。

macOS Cocoa 原生测试：**4 passed**，覆盖 CT、PET、融合 3D 的折叠/展开、工具栏宽度调整、独立右键菜单实际点击删除、保留原生视图和源文件、PNG 及 PET 裁剪/单位切换，以及窗口按钮。测试曾因调用 `QWindow.transientParent()` 引起 PySide 包装对象所有权异常；改为验证独立弹出窗口可见与菜单真实点击，不再调用该诊断接口，整组通过。Windows 原生桌面仍待实机验收。

日志：`/private/tmp/voxenra-rail-targeted.log`、`/private/tmp/voxenra-rail-native-final.log`。

最终完整回归：**937 passed, 19 skipped, 589 warnings**，耗时 177.72 秒，无排除项。日志 `/private/tmp/voxenra-rail-full.log`；跳过项仍为 15 项显式启用的 Docker/PACS 测试和 4 项原生桌面测试。警告仍为既有 VTK/NumPy 弃用及合成 DICOM 标签提示。

截图：`/private/tmp/voxenra-rail-full/test_compact_click_multiselect0/compact-series-view.png`、`/private/tmp/voxenra-rail-full/test_compact_context_keeps_sel0/compact-series-menu.png`。`git diff --check` 通过；修改保留于现有 worktree，尚未提交，main 未改动。

## 侧栏底部对齐与折叠入口补充（2026-09-09）

清空所有序列改用现有垃圾桶图标，保留提示与原有列表清空行为。展开状态的导出、清空、手册、设置及收起按钮统一在 36 px 底部行垂直居中。折叠状态保留 52 px 宽度，底部按手册、设置、展开排列，各占 36 px，序列滚动区止于底部操作区。顶部文件夹与 PACS 分别按对应数据源开关显示，不再共用一个入口。

相关真实 QML 回归 **48 passed, 1 skipped**，覆盖底部中心线一致、折叠入口点击、多选/右键、滚动稳定性、小窗口及数据源显隐，无 QML 布局或绑定警告。macOS CT、PET、融合原生 3D 回归 **3 passed**；菜单测试改为等待独立弹窗显示后检查，避免固定等待时间导致的偶发失败。本轮为局部界面修改，未重复运行完整 pytest。

日志：`/private/tmp/voxenra-footer-final.log`、`/private/tmp/voxenra-footer-native-final.log`。
截图：`/private/tmp/voxenra-footer-final/test_compact_click_multiselect0/expanded-footer.png`、`/private/tmp/voxenra-footer-final/test_compact_click_multiselect0/compact-series-view.png`。

## 原生窗口控制、全屏与绘制完成状态（2026-09-09）

窗口恢复系统原生装饰，移除手绘信号灯、字符形式的窗口按钮及自绘窗口缩放边缘。顶部品牌栏保留 32 px 深色背景；通过 Qt 6.9+ ExpandedClientAreaHint / NoTitleBarBackgroundHint 与系统按钮共存。Windows 启动时请求深色系统外观，使用系统最小化、最大化/还原、关闭按钮。最低 PySide6 版本更新为 6.9。

macOS 原生绿色按钮调用系统全屏，Control+Command+F 可切换全屏；Windows 使用 F11。最大化与全屏分开处理。macOS 刘海屏的系统安全区域仍由 AppKit 保留。原生测试实际调用本应用 NSWindow 的 standardWindowButton，检查信号灯可见、原生绿色按钮进入 NSWindowStyleMaskFullScreen、窗口宽度与屏幕一致且底部到达屏幕边缘，并验证退出、最小化和关闭。

长度、角度、矩形、椭圆、纯箭头和文字箭头在有效绘制完成后保留选中并停止新建；继续点击或拖动空白不会意外新增。点击“继续绘制”或重新选择工具可重新开始。测量和纯箭头已有编辑入口保持可用。角度仅在第三点完成后结束绘制，无效草稿不会结束绘制模式；MTF、QA 的范围工具保留现有行为。

序列右键菜单的 2D、MPR、3D、4D、Tag、平铺及融合图标与左侧导航一致。2D 平移、选中对象整体移动和十字线定位使用原生手形/抓手，3D 平移和旋转按住时使用抓手，失焦后恢复。其余操作使用单个居中光标，不再叠加箭头与右下徽标。操作手册同步说明新的绘制和光标行为。

验证：针对性真实 QML/控制器 **61 passed, 1 skipped**；macOS 原生窗口与 CT/PET/融合 3D **4 passed**；最终完整 pytest **942 passed, 19 skipped, 589 warnings**，耗时 177.91 秒，无排除项。19 项跳过仍包括 15 项显式启用的 Docker/PACS 测试和 4 项原生桌面测试。无 QML 布局或绑定警告；警告为既有 VTK/NumPy 弃用和合成 DICOM 标签提示。Windows 原生按钮外观、窗口贴靠和全屏仍待 Windows 实机验收，macOS 结果不能代替 Windows 验收。

日志：`/private/tmp/voxenra-controls-verified.log`、`/private/tmp/voxenra-native-controls.log`、`/private/tmp/voxenra-controls-final.log`。截图：`/private/tmp/voxenra-controls-final/test_compact_context_keeps_sel0/compact-series-menu.png`、`/private/tmp/voxenra-native-controls/test_native_window_maximize_re0/native-fullscreen.png`（QQuick 抓图不包含原生窗口装饰）。Qt 实现依据链接见 `docs/display-settings.md`。

`git diff --check` 通过。修改仍在现有 worktree，未提交；main 与原目录未跟踪验证资料保持原状。

最终截图复核发现原生扩展客户区下 `topPadding: 0` 会让工作区顶端进入标题栏。已将顶部内边距绑定为标题栏高度，并加入工作区不得越过标题栏底边的断言。修正后追加真实 QML 回归 **22 passed, 1 skipped**，原生 macOS 再次 **4 passed**，均无 QML 布局或绑定警告；此布局修正未重复完整 pytest。

最终布局日志：`/private/tmp/voxenra-chrome-inset.log`、`/private/tmp/voxenra-native-inset.log`。修正后的菜单截图：`/private/tmp/voxenra-chrome-inset/test_compact_context_keeps_sel0/compact-series-menu.png`；先前 `/private/tmp/voxenra-controls-final` 中的窗口截图被本轮截图取代。

## 紧凑工具区、连续绘制与光标修正（2026-09-09）

本轮替代上一阶段的“继续绘制”门控：有效拖动在松开时完成并保持选中，移动鼠标不会继续修改已完成结果，在空白处再次拖动即可新建。角度仍在第三点完成后提交；既有选中对象的移动、控制点编辑与删除入口保留。已移除继续绘制按钮及关联状态，更新操作手册。

右侧主工具按钮改为 36 px 高、2 px 间距、上下各 4 px 留白，宽度自适应最多六列，reset 顺序保持最后。列宽取整数，防止浮点误差导致最后一项意外换行并侵入内容区。折叠按钮改用几何中心一致的矢量箭头，展开与收起状态均验证图形中心，而非仅验证按钮矩形中心。

macOS 重影来自原生 NSWindow 标题与 QML 品牌同时绘制。仅在 Cocoa 平台通过 titleVisibility 隐藏原生标题文字，保留 Voxenra 窗口标题及原生信号灯，并在窗口状态变化后重新应用。实际验证全屏进入/退出后的原生 titleVisibility 仍为隐藏，绿色信号灯进入真正全屏，最小化与关闭正常。

平移改为短箭头的四向光标，平移和缩放共用 SVG 资源，原生 3D 按设备像素比生成相同图形，落点统一在 24 px 图形中心。分割和 VOI 新建保留系统箭头指针，在右下方偏移 (14, 18) px 显示 18 px 工具图标；箭头尖端仍是实际落点，选中范围的移动和尺寸调整继续使用对应光标。

验证结果：

- 完整 pytest：**955 passed, 19 skipped, 589 warnings**，179.30 秒，无排除项。初次完整回归的四处失败仅为旧测试仍要求按钮至少 44 px；同步紧凑尺寸要求后完整回归通过。
- macOS Cocoa 原生窗口及 CT/PET/融合 3D：**4 passed, 10 deselected, 6 warnings**。验证原生标题隐藏、信号灯、全屏、折叠与恢复、右键菜单、宽度拖拽、共享光标、PET 裁剪与单位切换及 PNG。
- 真实 QML 覆盖松开后提交/选中、连续创建、悬停不改动已完成结果、VOI/分割原生箭头与徽标落点、最窄 220 px 工具栏、按钮中心线和无布局/绑定警告。共享光标另外覆盖 100%、125%、150%、200% DPI 的逻辑尺寸与落点。
- 19 项跳过仍为 15 项需显式启用的 Docker/PACS 测试和 4 项单独执行的原生桌面测试。警告仍为既有 VTK/NumPy 弃用及合成 DICOM 私有标签提示。

日志：`/private/tmp/voxenra-latest-final.log`、`/private/tmp/voxenra-latest-native-fixed.log`。
截图：`/private/tmp/voxenra-latest-final/test_toolbar_placeholders_hove1/toolbar-mpr-220.png`、`/private/tmp/voxenra-latest-final/test_compact_click_multiselect0/expanded-footer.png`、`/private/tmp/voxenra-latest-final/test_pan_and_zoom_use_shared_c0/pan-cursor.png`。QQuick 抓图不包含系统光标和原生装饰；原生标题通过本应用的 AppKit 状态断言验证，箭头通过实际指针处理器的 cursorShape 验证。

`git diff --check` 通过。修改保留于 `codex/series-tools-polish` worktree，尚未提交；main 和原目录的未跟踪验证资料未修改。当前环境没有 Windows 桌面，原生窗口外观、全屏和光标的 Windows 实机验收仍待完成。


## 统一指针光标、导航快捷操作与变换信息（2026-09-09）

本轮统一替代此前的居中图标、手形及分割/VOI 特例：影像工具均使用一个箭头指针与右侧的当前操作小图标。QML 2D、MPR、4D、融合、平铺及原生 CT/PET/融合 3D 共用 SVG，逻辑尺寸 40 × 32 px、热点 (2, 2)、右侧图标 18 px。覆盖翻页、调窗、平移、缩放、旋转、测量、标注、QA、MTF、分割、VOI、范围移动/缩放和十字线交互；平移保留短箭头图形，按下及拖动不再切成不同风格。手册图例同步更新。

翻页二级面板提供首页、末页、前后 10 页，使用现有切片索引入口并遵守边界；MPR/4D 操作当前方向，4D 时相保持不变。不支持逐页浏览的视图禁用快捷操作。缩放二级面板提供绝对 1×、2×、5×、10×，1× 为默认适配大小，保持平移、旋转、显示参数及已完成裁剪。

默认右下角增加旋转/水平与垂直翻转信息，2D、MPR、PET、4D、融合及平铺随操作和重置实时更新；原生三维显示相对初始视角的 XYZ 旋转角度。四角信息设置支持隐藏、移动和样式配置，原生三维 PNG 包含此信息。只迁移旧版默认布局；配置增加版本标识，用户明确删除该字段后重启不会重新加入。Retina 原生文本按 VTK 实际 DPI 换算字号，避免重复放大。

验证结果：

- 受影响的真实 QML、控制器和光标回归：**183 passed**，随后增加导航及变换信息专项覆盖并纳入完整回归。
- 完整 pytest：**1047 passed, 19 skipped, 589 warnings**，190.48 秒，无排除项。跳过为 15 项需显式启用的 Docker/PACS 测试及 4 项原生桌面测试；警告为既有 VTK/NumPy 弃用和合成 DICOM 私有标签提示。
- macOS Cocoa 原生 CT、PET、融合 3D：**3 passed, 7 deselected, 12 warnings**，7.44 秒。验证统一光标及热点、按下状态、缩放快捷操作、旋转文字、Retina 文字边界、设置隐藏、PNG，以及原有侧栏折叠/展开、裁剪和单位切换。原生展开测试等待真实子窗口几何更新并激活主窗口后点击，避免只等待 QML 布局造成的偶发误点。
- 全部 21 类光标覆盖 100%、125%、150%、200% DPI；真实 QML 覆盖快捷按钮边界、绝对缩放、跨页签独立、PET MPR、4D 当前时相、变换重置及配置重启恢复，无布局或绑定警告。

日志：`/private/tmp/voxenra-tools-new-fixed.log`、`/private/tmp/voxenra-tools-full.log`、`/private/tmp/voxenra-tools-native-verified.log`。
截图复核：`/private/tmp/voxenra-tools-new-fixed/test_pan_and_zoom_share_pointe0/pan-cursor.png`、`/private/tmp/voxenra-tools-shortcuts-final/test_zoom_buttons_set_absolute0/zoom-shortcuts.png`、`/private/tmp/voxenra-tools-native-pet/test_native_volume_sidebar_dra0/pet-3d.png`。QQuick 抓图不包含原生 VTK 子窗口；三维 PNG 通过原生渲染捕获验证。

修改保留在现有 `codex/series-tools-polish` worktree，未提交；main 及原目录未跟踪验证资料未修改。当前环境没有 Windows 桌面，Windows 原生光标外观仍待实机验收。


## 原生顶部外观、图标抗锯齿与 CT/平铺显示（2026-09-09）

原生装饰请求深色颜色方案。macOS 对当前 NSWindow 应用 Dark Aqua、透明标题栏和与 QML 相同的背景色，延续标题文字隐藏和窗口状态变化后的重新应用；保留原生信号灯及全屏。标题 logo 按屏幕 DPR 请求纹理。设置、关闭、折叠等原 Shape 图形和伪彩图标改走共享 SVG 管线，先按目标物理尺寸的 2 倍渲染后平滑缩小；按钮图文垂直对齐，伪彩列表高度收紧且在拖动宽度后重绘渐变。

平铺提供完整伪彩选择，并沿用普通/PET 默认色表。色表和反白更新复用已解码模态像素；请求版本拒绝旧结果，新进入可见区的切片采用当前显示。顶部列数旁新增详情收起/展开按钮，默认展开，当前页签保留状态。收起保留标题、切片数、窗值、模态、列数及展开入口；隐藏患者/检查/扫描详情。窄窗口自动将操作放入第二行，并将详情排为两列。

CT 2D、MPR、4D、平铺、融合及 CT/融合 3D 调窗面板新增「反白」，高亮反映当前状态，再次点击恢复。CT 3D 和融合 3D 打开调窗二级面板，可输入/应用窗值。反白不改源数据与 WW/WL；二维在伪彩映射前反转灰度，原生三维反转 CT 颜色并保持透明度、裁剪和 PET 层。MPR/4D 沿用同页签联动；融合采样缓存键包含 CT 反白状态，失败时回滚至最后成功状态。融合 3D 窗值与反白独立于源融合页签，源页签关闭后仍可操作。调窗重置及全部重置关闭反白。

验证结果：

- 新增像素/状态与真实 QML 针对性回归：**30 passed, 1 skipped**。覆盖平铺缓存复用、伪彩/反白像素、过期请求、WW/WL 保持、MPR/4D 三方向与时相、融合 PET 层不变、失败回滚、三维颜色与透明度、详情切换。
- 最终完整 pytest：**1058 passed, 19 skipped, 589 warnings**，190.48 秒，无排除项。首轮两项失败为旧断言要求融合 3D 无调窗工具及 CT 3D 无调窗面板；更新后完整回归通过。
- macOS 原生 CT/PET/融合 3D：**3 passed**；CT 与融合验证实际 PNG 反白发生变化、再次切换与原图完全一致，窗值不变；原有侧栏、裁剪、单位及变换信息检查通过。
- macOS 原生窗口：**1 passed**，验证实际 AppKit effectiveAppearance 为 Dark Aqua、透明标题栏、系统信号灯、全屏进入/退出、最大化、最小化与关闭。最初新增断言导入了错误的测试辅助函数，修正为同文件函数后通过。
- 图标覆盖 100%、125%、150%、200% DPI、透明度、颜色及边缘中间 alpha；平铺 360 px 窄视图和详情切换滚动误差不超过 1 px。无 QML 布局/绑定警告。跳过项为 15 项需显式启用的 Docker/PACS 测试和 4 项单独运行的原生桌面测试；警告为既有 VTK/NumPy 弃用与合成 DICOM 私有标签提示。

日志：`/private/tmp/voxenra-display-complete-fixed.log`、`/private/tmp/voxenra-visual-final.log`、`/private/tmp/voxenra-visual-native.log`、`/private/tmp/voxenra-chrome-dark-native.log`。
截图复核：`/private/tmp/voxenra-display-complete-fixed/test_montage_real_palette_inve0/montage-expanded.png`、`/private/tmp/voxenra-display-complete-fixed/test_montage_real_palette_inve0/montage-collapsed-inverted.png`、`/private/tmp/voxenra-visual-native/test_native_volume_sidebar_dra2/fusion-3d-inverted.png`。原生装饰通过 AppKit 属性与原生按钮验证，QQuick 抓图不能单独验证操作系统窗口边框。

`git diff --check` 通过。修改保留在现有 worktree，未提交；main 和原目录验证资料未修改。当前没有 Windows 桌面，Windows 原生外观仍需实机验收。


## 0.3.0：绘制完成样式、稳定窗值输入、三维精简与匿名导出（2026-09-09）

继续在 `codex/series-tools-polish` 上修改，保留此前功能。程序、pyproject 和 uv.lock 的本地包版本统一为 0.3.0；设置导航在「工作区设置」下显示 Voxenra 0.3.0。

测量数据在松开时原本已提交，但选中状态仍触发编辑色/虚线。现仅正在绘制或拖动编辑的临时几何使用编辑样式；完成并选中时使用完成线型，保留控制点及删除能力。长度、角度、矩形、椭圆及箭头采用 Shape CurveRenderer 与抗锯齿、圆形端点/连接。平铺宫格仅显示切片序号，不再显示 Rot/Flip。调窗 WW/WL 输入框使用等宽列和 32 px 固定高度，长数值、负值、小数、预设更新和编辑均不改变控件尺寸。

所有原生 3D 移除反白入口及其独有反转代码、四角文本 actor 和旋转读数；保留 CT/融合三维独立窗值、模板、裁剪及方向立方体。二维 CT、MPR/4D、平铺及融合切片的反白保留。

右侧 PNG/DICOM 导出新增默认勾选的匿名选项。DICOM 复用现有 Anonymizer，保留源像素与一致的跨实例 UID 映射；取消勾选后复制原始字节。PNG 在后台检查所有相关源实例的身份像素标记，匿名截图临时隐藏四角自由文字、文字标注和平铺患者/检查详情，保留测量和箭头几何，清除文本元数据。截图成功、取消、失败后恢复显示，不改设置、标注数据或源文件。检查期间关闭或切换页签会停止截图；请求标识阻止迟到截图回调写入后续导出。沿用既有烧录文字/可识别外观/嵌入叠加层拦截，不自动识别或擦除原始像素内的身份内容。

左下角导出入口与弹窗「开始导出」采用蓝色主操作样式；更改位置采用描边按钮，关闭采用低强调文字按钮。同步更新设置说明及应用内操作手册。

验证结果：

- 最终完整 pytest：**1079 passed, 19 skipped, 589 warnings**，210.57 秒，无排除项。19 个跳过项仍为 15 项需显式启用的 Docker/PACS 场景和 4 项原生桌面场景；警告为既有 VTK/NumPy 弃用与合成 DICOM 私有标签提示。首轮四条旧断言仍要求已提交但选中的测量使用编辑色，按新交互更新后全量通过。
- 测量设置、绘制完成、版本及匿名导出专项：**31 passed**。真实指针覆盖六种测量/标注方式、完成后选择及删除、重新拖动编辑；真实图片验证完成色与线型。窗值输入在 220/250/420 px 侧栏内等宽且保持尺寸，覆盖极值、小数、负数及逐字编辑。
- 匿名 PNG 真实像素与身份处理专项：**9 passed**（纳入完整回归），覆盖四角及标注自由文字消失、平铺详情匿名且保持展开状态、成功/失败/取消恢复、检查中切换或关闭、迟到回调、已有文件保护及源文件不变。匿名与非匿名真实导出面板覆盖 2D、MPR、平铺及窄窗口；整序列 PNG/DICOM 既有匿名回归通过。
- macOS 原生 **Metal / DPR 2.0：5 passed**，检查长度、纯箭头、角度、矩形、椭圆细线均有足够的中间覆盖灰度，截图复核平滑边缘。软件路径也纳入完整 pytest。
- macOS Cocoa 原生 CT、PET、融合 3D **各 1 passed**。验证无反白按钮、无四角文本 actor，四角设置变化不改变原生像素；方向立方体保留。默认匿名 PNG 与当时原生画面像素一致，并继续验证侧栏折叠/展开、右键、PET 裁剪和单位切换。首次同一进程连续测试的 PET/融合用例在主窗口激活等待处超时；各类单独进程完整复测均通过。
- 真实 QML 检查没有布局/绑定警告；`git diff --check` 通过。导出对话框、1000 px 窗口的导出面板、设置版本显示及原生 PNG 均做截图复核。

日志：`/private/tmp/voxenra-030-final.log`、`/private/tmp/voxenra-030-corrected.log`、`/private/tmp/voxenra-anonymous-proof.log`、`/private/tmp/voxenra-montage-anonymous.log`、`/private/tmp/voxenra-antialias-metal.log`、`/private/tmp/voxenra-native-ct-final.log`、`/private/tmp/voxenra-native-pet-final.log`、`/private/tmp/voxenra-native-fusion-final.log`。

截图：`/private/tmp/voxenra-030-full/test_export_dialog_defaults_fo0/dicom-export-dialog.png`、`/private/tmp/voxenra-030-full/test_version_matches_runtime_b0/settings-version.png`、`/private/tmp/voxenra-antialias-metal/test_thin_diagonal_and_curved_0/length-antialias.png`、`/private/tmp/voxenra-native-fusion-final/test_native_volume_sidebar_dra0/fusion-3d-anonymous-export.png`。

修改未提交；main 和原目录的未跟踪验证资料保持原状。当前环境没有 Windows 桌面，Windows 实机外观仍未验收。本次更新源代码版本，未打包或发布安装包。
