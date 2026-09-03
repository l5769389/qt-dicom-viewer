# 服务图标

这三个 PNG 使用内置 imagegen 生成，没有使用 CLI，也没有用 SVG 重绘。
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
