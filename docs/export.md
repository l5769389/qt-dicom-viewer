# 序列导出

## 使用

1. 在左侧选择一个序列，点击底部的导出图标（提示为“导出序列”）。
2. 选择 DICOM 或 PNG；匿名每次默认开启，可在普通导出中取消。
3. 检查导出位置，点击“开始导出”。完成后点击“打开文件夹”。

右键“脱敏导出整个序列…”锁定匿名选项，目标为右键所指的一个序列。
即使当前打开了另一个序列的视口，或者列表中多选了其他序列，也只导出该目标序列。
导出所有实例（含所有相位）；PNG 还会展开每个多帧实例。
扫描期间入口不可用，避免导出尚未扫描完成的序列。

“设置 → 导出”保存全局导出目录。默认值通过 Qt 的系统文档目录解析，为
`<Documents>/Voxenra/Exports`。目录按需创建，每次导出新建独立子目录，
名称和输出文件名不使用患者信息、原文件名或原始 UID。

右侧视口导出面板使用“导出 PNG”和“导出 DICOM”文字按钮，并提供默认勾选的“匿名导出”。匿名 DICOM 使用与整序列导出相同的身份清理规则；取消勾选后才逐字节复制原文件。匿名 PNG 隐藏四角文字、自由文字标注及平铺的患者/检查详情，并清空图像文本元数据；保留影像显示参数、测量线段和箭头几何。3D 使用当前原生画面，包含裁剪结果和方向立方体。

PNG 身份检查在后台执行；截图只临时改变导出目标的文字显示，成功、失败或取消后立即恢复，不改全局设置或标注数据。检查期间关闭或切换目标视图会停止该次截图。两种匿名导出均检查源文件的烧录文字/可识别外观标记，并沿用下文的限制。

左下角导出入口和对话框“开始导出”使用蓝色主操作样式；更改位置使用描边按钮，关闭使用低强调文字按钮。

## 格式

| 格式 | 图像及元数据行为 |
| --- | --- |
| 匿名 DICOM | 保留原始像素编码、多帧、几何和灰阶变换；处理元数据并重建文件头 |
| 非匿名 DICOM | 逐字节复制原文件，包含原始身份信息 |
| 匿名 PNG | 每帧一个原始分辨率图像，无患者文本元数据 |
| 非匿名 PNG | 与匿名 PNG 使用相同图像，附带 PatientName、PatientID、StudyInstanceUID、SeriesInstanceUID 文本元数据 |

PNG 使用影像内的 Modality LUT / Rescale、VOI LUT 或窗宽 / 窗位；增强多帧读取共享及逐帧变换。
无窗信息时使用该帧的有限像素范围。支持 MONOCHROME1 反相、RGB 和调色板。
它导出源序列，不是当前视口截图；不包含 MPR / 3D 重建、视口伪彩、缩放、旋转或测量标注。
压缩 PNG 解码依赖当前 pydicom 环境可用的解码器；缺少解码器时整次导出失败并清理临时文件。
DICOM 导出不需要解压像素。

## 匿名范围

内置规则来自 [DICOM PS3.15 2026c Table E.1-1](https://dicom.nema.org/medical/dicom/2026c/output/chtml/part15/chapter_E.html#table_E.1-1)。
按标签递归执行删除、置空、替换或 UID 映射；补充处理私有及未知属性、姓名、日期、时间和自由文本。
包含原始属性、加密属性、签名、图标图像、曲线和叠加层的载荷被移除。
替换文件前导区和 File Meta Information，并同步 SOP Instance UID。
患者 ID 和 UID 映射仅在一次导出中保留；重复导出产生不同标识，不保存反向对应表。

标准 SOP Class UID、传输语法、代码系统等语义标识保留。
同一导出中 Study、Series、Frame of Reference 及 SOP Instance UID 的映射一致，
保留的 Referenced Image / Source Image 引用也使用相同映射。
匿名 DICOM 写入 `PatientIdentityRemoved=YES`，并在 `DeidentificationMethod` 明确说明像素未清理。
没有声明实现所有 IOD 的合规验证；替换描述、患者体重、日期和私有字段后，某些后处理（例如 PET SUV 重算）可能不可用。

匿名仅支持标准 Image Storage 对象；私有 SOP Class、封装文档和结构化报告不支持匿名导出。
普通非匿名 DICOM 仍可复制这些对象。

**不会检测或擦除像素中烧录的文字，也不执行人脸去除。**
像素清理在 DICOM 中属于独立的 [Clean Pixel Data Option](https://dicom.nema.org/medical/dicom/current/output/chtml/part15/sect_E.3.html)。
本功能不声明实现该选项。若任一实例声明 `BurnedInAnnotation=YES`、
`RecognizableVisualFeatures=YES` 或含嵌入像素的旧式叠加层，匿名导出整次拒绝，要求先处理像素。
这些标签缺失或值为 NO 并不能证明像素无身份信息，用户应核对影像内容。

## 验证

`tests/test_series_export.py` 覆盖显式 / 隐式 VR、RLE 压缩、像素和几何不变、文件头 / 私有 / 嵌套标签处理、
跨实例 UID 引用、匿名和非匿名 PNG、多帧、RGB / 调色板、逐帧窗、目录持久化、取消与失败回滚。
`tests/test_export_qml.py` 从真实 QML 入口执行两种格式导出，验证默认匿名、右键锁定匿名、设置编辑，
并在 1000×600 下检查主要控件可见且无 QML 警告。

右侧原有导出工具继续提供当前视口 PNG 截图和原始 DICOM 复制，由 `tests/test_export.py` 验证；其任务状态与左侧整序列导出独立。
