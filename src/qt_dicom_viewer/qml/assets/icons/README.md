# 界面图标

## 当前运行时版本

操作与导航使用 SVG，通过 `SvgIconProvider` 按屏幕像素密度渲染、随状态着色；伪彩使用 QML 矢量色带。当前轮廓以用户确认的旧版工具栏截图为基准，采用较清晰的描边与少量实心面。详见 `docs/button-review/README.md`。

以下 PNG 说明与生成提示词保留为历史资料，不代表当前功能状态或运行时实现。

## 图像操作图标

`tool-*.png` 是新版独立透明 PNG，与导航采用同一白色平面风格。
AppIcon 统一按默认灰色、选中青色、悬停与禁用状态着色。
测量、服务、MTF、MIP 已替换现有入口；伪彩、融合、去床板、
MPR 的分割、VOI 已接入绘制与定量面板；3D 的 VOI 仍是禁用占位入口。
两侧工具栏统一使用 ToolbarAction，默认灰蓝、选中青色，附短标签；
占位入口带“待”标记，并在悬停时提示“待实现”。
完整语义检查、接入范围和生成提示词见 `docs/tool-icon-design.md`。

## 导航视图图标

以下文件是一套透明底 PNG 导航图标，2026-09-06 使用内置 ImageGen 更新。
最终版采用白色平面线框与少量实心面，去掉立体材质、阴影与橙色，
匹配深色工作站界面；线框在实际工具栏尺寸下经过加粗调整。
图标为独立资产，不包含按钮边框或容器背景，已接入左侧两行操作区。

- `nav-load-file.png`：加载 DICOM 文件
- `nav-view-2d.png`：2D 切片视图
- `nav-view-mpr.png`：MPR 三正交切面
- `nav-view-3d.png`：3D 体数据
- `nav-view-tile.png`：平铺视图
- `nav-view-4d.png`：4D 时间相位体
- `nav-view-tag.png`：DICOM Tag

界面顺序：第一行文件、2D、MPR、3D；第二行平铺、4D、Tag、融合。
源图为 RGBA PNG（多数为 1254 × 1254，Tag 为 1284 × 1225），
由 Qt 保持比例按控件尺寸平滑缩放。
最终版提示词见 `docs/navigation-icon-monochrome-prompts.md`。
当前主分支尚未实现平铺功能，其入口保持禁用。

## 历史服务图标（保留源文件，不再由 AppIcon 使用）

以下描述仅对应旧版。这三个 PNG 使用内置 imagegen 生成，没有使用 CLI，也没有用 SVG 重绘。
QML 直接加载图片，不改变图片颜色；按钮的边框和底色表示选中状态。

- `mtf.png`：沿用用户确认的圆环、半填充方块、虚线十字版本。深色底，无透明通道。
- `service.png`：六角工具框与扳手，带透明通道。
- `qa.png`：盾牌与对勾，带透明通道。

原图均为 1254 × 1254，由 Qt 缩放显示。当前仅用于服务菜单入口，不表示对应计算功能已实现。

## MTF 最终编辑提示词

输入为前一版 MTF 生成图，最终使用深色底版本。

```text
Redraw this MTF toolbar icon as a finished clean flat raster icon preview. Preserve the same centered circular ring, upright centered square with its left half filled white and right half unfilled, and dashed crosshair axes. Replace EVERY bit of the checkerboard with one perfectly uniform solid very dark navy background #07131c, also inside all negative spaces and dash cutouts. Strong crisp pure white artwork, medium-bold smooth clean edges, no mottling, no texture, no gradients, no checkerboard, no transparency simulation, no glow, no shadows, no 3D, no text. Single icon only, on a square canvas, evenly padded, professional medical imaging workstation visual style. Keep exactly these elements and remove all accidental artifacts.
```

## 服务生成提示词

```text
Use case: logo-brand. Asset type: a single raster toolbar icon for Services in a professional dark medical imaging workstation. Draw a clean white outlined hexagonal mechanical nut surrounding a simple diagonal open-end wrench, forming one coherent compact service/maintenance emblem. Minimal flat monochrome geometry, balanced centered symmetry, clear strong silhouette readable at 24 pixels, thick consistent strokes, rounded joins, ample space between wrench and outline. Square canvas, symbol uses 82 percent of width. One perfectly uniform solid dark navy #07131c background. White artwork only. No words, no letters, no logo text, no gradients, no shadows, no glow, no texture, no checkerboard, no 3D, no additional elements.
```

## QA 生成提示词

```text
Use case: logo-brand. Asset type: a single raster toolbar icon for QA in a professional dark medical imaging workstation. Draw a clean white outlined shield with one bold centered check mark, indicating quality assurance. Minimal flat monochrome geometry, balanced centered symmetry, clear strong silhouette readable at 24 pixels, thick consistent strokes and rounded joins, ample space between check mark and shield. Square canvas, symbol uses 82 percent of height. One perfectly uniform solid dark navy #07131c background. White artwork only. No words, no letters, no logo text, no gradients, no shadows, no glow, no texture, no checkerboard, no 3D, no additional elements.
```
