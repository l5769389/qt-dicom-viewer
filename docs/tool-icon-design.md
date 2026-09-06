# 图像工具栏图标（2026-09-06）

使用内置 ImageGen 逐张生成，没有使用 CLI、SVG 重绘或拼图切割。每个最终资产为独立 1254 × 1254 RGBA PNG，保留原始生成文件。使用白色平面轮廓与实心面，不自带按钮背景；由 AppIcon 根据 UI 状态统一着色。Qt 按实际 22px 工具栏尺寸显示。

## 语义与接入范围

| 文件（assets/icons/） | 语义 | 当前接入 |
|---|---|---|
| tool-fusion.png | 两图层重叠，强调融合区域 | 左侧第二行禁用占位 |
| tool-pseudocolor.png | 灰度映射坡道与查找表 | 2D / MPR / 4D 工具栏禁用占位 |
| tool-measure.png | 圆规与角度弧，代表综合测量 | 替换一级测量；长度子工具仍用尺子 |
| tool-service.png | 齿轮与服务加号 | 替换服务入口 |
| tool-mtf.png | 随空间频率下降的响应曲线 | 替换 MTF 入口 |
| tool-remove-bed.png | 断层轮廓与待移除的床板 | 3D 工具栏禁用占位 |
| tool-segmentation.png | 区域轮廓与内部掩膜 | MPR 工具栏禁用占位 |
| tool-voi.png | 外部体积中选择的内部小体积 | MPR / 3D 工具栏禁用占位 |
| tool-qa.png | 盾牌对勾 | 服务面板禁用占位 |
| tool-mip.png | 多层切片到输出面的投影 | 替换 MIP 入口 |

窗宽窗位、翻片、平移、缩放、旋转、标注、重置的现有符号语义明确，保留轮廓并使用相同状态色。3D 的调色板代表体渲染预设，与伪彩 LUT 区分；方向字母保留有意义的方向颜色。根据后续要求，未实现功能以禁用按钮占位，不新增图像处理行为。标注空面板也改为禁用占位。

## 通用提示词

```text
Use case: logo-brand. Create one production toolbar GLYPH for a dark DICOM viewer, not an illustration. White flat monochrome raster PNG with REAL TRANSPARENT ALPHA background. Square canvas. Symbol occupies 80% canvas centered with equal padding. All strokes BOLD AND CLEAN about 65px thick on a 1254px canvas (1.7px at 32px display). Straight clean geometric lines, small rounded joins, open negative space. Pure opaque white shapes. Match conventional professional medical software line icons. NO shading, NO gradients, NO extrusion, NO glossy material, NO 3D render, NO shadow, NO orange or other color, NO words, NO watermark, NO button tile, NO enclosing rounded-square border. No painted checkerboard. Exactly one clear compact symbol, readable at 24px.
```

## fusion

```text
Two offset overlapping outlined square image planes. Their shared overlapping central square is solid white, nonoverlapping areas transparent. Clear union of two aligned image modalities. Only two squares and overlap, no arrows.
```

## pseudocolor

```text
A simple horizontal lookup-table strip divided into four adjacent broad cells, beneath a small outlined triangular ramp increasing left to right. All monochrome white: alternate filled and unfilled cells to suggest remapping intensity bins. Compact LUT palette symbol, no paint palette, no droplet.
```

## measure

```text
An open technical drafting compass with two splayed legs, a small hinge at top, and a short angle arc between its legs. Simple geometric measurement-instruments symbol representing general measurement, NOT a ruler or length-only tool.
```

## service

```text
A clean outlined gear with six broad teeth, containing a tiny four-square grid of analytical modules at center. Crisp symmetric toolkit hub, no wrench, no hex nut, no outer frame.
```

## mtf

```text
An L-shaped plot axis with ONE thick smooth descending response curve: starts high almost horizontal at left, curves down through middle and flattens near lower right. Two tiny axis ticks maximum. Scientific modulation transfer response chart glyph, no letters, no waveform, no circular target.
```

## remove-bed

```text
A simplified rounded patient cross-section floating above a detached thin horizontal scan table plank. A clear gap separates body and table. Put a small X at the right end of the table plank to signify removal of the table only. Body remains intact. No human figure, no hospital bed wheels.
```

## segmentation

```text
One irregular closed region contour with a smaller irregular white solid region inside and a small disconnected outline region beside it. A short dashed boundary segment differentiates regions. Medical mask segmentation silhouette, no scissors, no scalpel, no enclosing frame.
```

## voi

```text
An isometric thin white outlined cube with intentionally open outer corners and a small solid white inner cube centered within. Clearly a selected three-dimensional volume inside a larger volume. No crosshair, no letters, no enclosing button.
```

## mip

```text
Exactly three short parallel vertical white projection arrows passing downward through two thin horizontal slice-plane lines into one solid horizontal output line below. A simple projection-through-slabs glyph, not an eye, no graph axes.
```

## qa

```text
A simple white outlined shield containing a single bold checkmark. Clean minimal quality-assurance glyph, no bevel, no gradient, no badge backing.
```

## 实际尺寸检查后的细化版

测量、服务、MTF、伪彩、去床板、分割采用以下第二轮生成结果；其余采用上面的首轮结果。保持独立透明 PNG，仅加粗与简化细节。服务最终语义为齿轮加号（分析服务）；测量为无多余关节的圆规。

```text
Use case: logo-brand. One small toolbar raster icon for a dark medical workstation. TRUE TRANSPARENT background with alpha; pure WHITE opaque symbol. Extremely simple BOLD FILLED geometric glyph, consistent solid 100px-thick strokes on a square 1254px canvas, with broad negative spaces. Centered symbol 80% of canvas, no frame. It must remain clear at 22px. NOT outlined silhouettes of thick strokes: the strokes THEMSELVES must be entirely filled opaque white. No thin hairlines, no doubled edges, no texture, no scratches, no speckles, no checkerboard, no gray, no shading, no 3D, no text, no watermark. 
```

### measure

```text
A stylized drafting compass, only two simple splayed solid bars, ONE circular pivot hole at top, and ONE thick short arc between the bars. NOT a realistic compass: no screws or hinges along the legs. Broad clean geometry.
```

### service

```text
One bold solid six-tooth gear with a single large transparent circular hole. Inside that hole a single solid plus sign for analytical services. No double contour, no grids, no extra concentric rings.
```

### mtf

```text
Only a bold L-shaped pair of graph axes and one thick smooth descending response curve. Curve high and horizontal at left, bends down in center, low and horizontal at right. LARGE gap between curve and axes. No ticks, no dots, no labels.
```

### pseudocolor

```text
A simple lookup table remapping icon: a solid right-triangle ramp rising left to right on top, and THREE broad separate rectangular swatches in one row below. Middle swatch is unfilled with bold white border; other two solid white. Very simple graphic, no thin strokes.
```

### remove-bed

```text
An ABSTRACT patient cross-section above a table: one thick simple oval outline containing ONE solid small oval. A clearly separated thick horizontal table bar below with a LARGE x at its right end. No anatomy, no organs, no bones, no brain detail, no textured scan.
```

### segmentation

```text
One bold simple irregular closed contour with ONE small solid irregular mask inside. A separate short dashed contour segment at right of the main region. No organic anatomical details, no multiple concentric loops, no pencil or scissors.
```
