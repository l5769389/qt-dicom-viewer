# 合并与操作手册验证记录

验证日期：2026-09-07。使用合成影像，不含真实患者资料。

## 提交与范围

- `37a306f`：提交 `codex/mpr-segmentation-voi` 的分割、VOI、光标、原手册与测试资源。
- `5d98f54`：合并 segment 到 main，解决右侧工具面板和底部重置区的重叠修改，保留 main 的 SVG、配色、导出与紧凑布局。
- 手册改造在合并后另行提交，增加唯一工作区页签、底栏书本入口、测量帮助、31 章离线内容和合成测量示例。
- `git merge-base --is-ancestor codex/mpr-segmentation-voi main` 通过。segment worktree 提交后干净；其他 worktree、分支及原有无关文件保留，未推送远端。

## 检查结果

| 检查 | 结果 |
| --- | --- |
| 合并后分割/VOI、测量 QML、导出集成 | 73 项通过 |
| 手册与 CT/PET 分割界面专项 | 10 项通过 |
| 工具栏/平铺入口兼容检查 | 15 项通过 |
| 最终完整回归 | 794 项通过，15 项跳过，138.40 秒 |
| QRC 编译、差异空白检查 | 通过 |
| 离线 wheel 构建及读取 | 31 章 JSON、手册 QML、SVG、全部示例 PNG 均包含；从解包 wheel 可读取测量章节 |
| 界面 | 1000×600、1400×900；普通及 2× 像素密度截图已检查 |

完整回归命令：

```bash
PYTHONPATH=src QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software \
  .venv/bin/python -m pytest -q -rs
```

15 项跳过均属于需显式开启的 Docker PACS 实验室测试，其中一项还需要原生桌面/OpenGL。常规本机 HTTP PACS 的成功、认证、超时、取消、查询、导入回归已运行。582 条警告来自 VTK 调用 NumPy 的弃用接口。

一次完整复跑在 `test_volume_panel_qml.py` 加载 QML 时发生 Qt 原生层 `SIGSEGV`，堆栈位于 `QV4::QObjectWrapper::getProperty`。随后该面板及后续相关测试隔离运行 63 项通过，再次完整运行 794 项全部通过。没有确定该间歇异常的根因，不将复跑通过表述为已修复原生崩溃。

手册测试验证无影像打开、唯一页签、搜索、所有章节/示例、工具章节直达、阅读位置恢复、后台关闭、最后关闭、最近使用页签返回。真实 MPR 鼠标绘制的测量和分割在手册往返后保留。3D 往返测试检查视角和显示控制器状态，隔离原生窗口创建；VTK 渲染与编辑由既有专项测试覆盖。

## 功能边界

- 测量、标注和 MPR 范围仅在对应影像页签的会话内保存；显示样式持久化。
- PNG 记录可见显示；DICOM 导出复制原始序列，不写入测量、标注、分割或裁剪。
- 未提供 DICOM SR、SEG/RTSTRUCT 导入导出、自由手绘三维分割、分割表面生成。
- MPR 支持矩形柱体阈值分割与球体/旋转椭球 VOI；3D 页签 VOI 仍为禁用占位，PET MIP 不用于范围绘制。
- MTF 和水模 QA 显示分析结果，不自动作合格判定。

## 截图

- [操作手册 1400×900](manual-1400.png)
- [操作手册 1000×600](manual-1000.png)
- [1000×600，2× 像素密度](manual-1000@2x.png)
- [测量章节与合成示例](measurement-1400.png)
- [鼠标交互与矢量光标图例](interaction-1400.png)
