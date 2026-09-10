# MPR 十字线与 3D 旋转性能验证

2026-09-10，在 macOS arm64 原生 Cocoa / QML 窗口测试。基线为
`810325b` 的 `MprReslicer`；对照仅替换重采样器，保留同一套控制器、
后台工作线程和 QML。使用 457 × 512 × 512 的合成 CT，轴位输出 512 × 512，
另两平面为 457 × 512。排除首次解码，保留正式加载缓存的指纹检查。

## 原因与修改

十字线旋转有源视图的反向平面补偿，因此当前图像无需重新采样，只更新另外
两幅图像；十字线本身也会立即响应目标角度。MPR 工具栏的“3D 旋转”改变整个
坐标架，三幅图像都要重新采样。两者的指针角度计算很轻，主要开销在插值。

原采样器为整幅图像创建坐标、索引、八组邻域值和权重数组。现在按约 16K 输出
像素分块，对连续体数据共用平面索引，避免重复的三维高级索引计算。有限值
邻域使用可分离的三线性插值，缺失邻域继续按有效权重归一化。

输出网格、物理间距、插值方式和 float64 中间计算精度保持一致，仍输出 float32。
没有降低拖动分辨率，也没有新增打包依赖。原有请求合并与最终角度提交机制保持不变。

## 实测

以下为同一设备的样本结果，不代表所有数据或 Windows 设备的帧率。
`sampling` 是纯重采样一轮所需时间：三方向轮流发起，共 30 个预热后的样本。

| 操作 | 基线中位数 | 优化后中位数 | 基线 P95 | 优化后 P95 |
| --- | ---: | ---: | ---: | ---: |
| 十字线旋转（两幅） | 40.66 ms | 16.59 ms | 51.00 ms | 18.23 ms |
| MPR 3D 旋转（三幅） | 61.27 ms | 23.90 ms | 71.39 ms | 24.71 ms |

重采样临时分配峰值（`tracemalloc`，不含预先加载的体数据）从 **48.51 MiB**
降至约 **5.03 MiB**。该数值不是整个应用的 RSS。内存测量单独进行，不干扰计时。

真实 QML 测试分别在三个视口发起两种旋转，各 60 次鼠标移动、约 8 ms 一次。
请求到图像更新的中位耗时如下；后台仍会合并来不及处理的输入，不能把图像
上传次数或窗口 `frameSwapped` 次数直接当作三视图完成帧率。

| 操作 | 源视口 | 基线 | 优化后 |
| --- | --- | ---: | ---: |
| 十字线 | 0 / 1 / 2 | 40.49 / 26.85 / 46.59 ms | 19.74 / 16.41 / 20.90 ms |
| 3D 旋转 | 0 / 1 / 2 | 41.67 / 48.01 / 58.11 ms | 23.16 / 24.20 / 28.15 ms |

鼠标松开到所有最新结果完成：3D 旋转从 53–131 ms 降至 31–42 ms。
六组拖动都验证三幅图像的最终采样方向与最新目标状态一致；没有 QML 警告或
加载失败。原始计时分别见 [before.json](before.json) 与 [after.json](after.json)。

## 回归与复现

新增标量八邻域参考验证，覆盖单体素轴、倾斜采样、跨分块偏移、体素边界与
浮点容差、NaN / 正负无穷、非连续数组、微小 PET 值及大幅度有符号数值。
完整隔离 pytest 覆盖 88 个文件，共 1218 项：1195 通过、23 跳过、0 失败。
覆盖既有 CT / PET / 融合 / 厚层 / 4D 回归；逐文件结果见
[regression.json](regression.json)。跳过项不计为已验证的跨平台原生行为。

在安装开发依赖后，从仓库根目录运行：

```sh
git show 810325b:src/qt_dicom_viewer/core/mpr_reslicer.py > /tmp/mpr-before.py
QT_QPA_PLATFORM=cocoa PYTHONPATH=src python tests/manual/benchmark_mpr_rotation.py /tmp/mpr-before.json --reslicer-source /tmp/mpr-before.py
QT_QPA_PLATFORM=cocoa PYTHONPATH=src python tests/manual/benchmark_mpr_rotation.py /tmp/mpr-after.json
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software PYTHONPATH=src:tests python tests/run_isolated.py --output /tmp/mpr-tests
```

Windows 上使用对应环境变量语法，将原生 GUI 的 Qt 平台改为 `windows`。
基准会打开并关闭自己的测试窗口，不需要临床数据。
