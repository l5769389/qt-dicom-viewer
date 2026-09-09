# 0.4.0：拖拽、压缩导入与窗值精度验证

环境：macOS Apple Silicon，Python 3.13.14，PySide6 6.11，VTK 9.5.2，pydicom 3.0.2。继续使用 series-tools-polish worktree；上一轮 0.3.0 已提交为 `068f381`，新版本分支为 `codex/import-compressed-dicom`。

## 覆盖内容

- ZIP、7z、TAR、TAR.GZ、TAR.BZ2、TAR.XZ、GZ、BZ2、XZ；中文路径、嵌套、重复输入、损坏 / 加密包、链接与越界路径、体积上限、取消与缓存回收。
- 真实 QML 的文件 / 文件夹 / ZIP / 7z 拖入、复制语义、拒绝远程 URL 和仅移动拖入、导入期间取消、多选文件对话框、错误提示关闭。逐次补入相同序列的切片，清空列表后重新导入单张仍保留完整序列及已打开视图。
- 合成 RLE、JPEG-LS 无损 / 近无损、JPEG 2000 无损 / 有损、Deflated 文件：校验解码像素、模态值、缩略图、体数据与匿名 DICOM 导出。另使用 pydicom 自带 JPEG Baseline、Extended、Lossless 等参考文件，不下载测试数据。
- WW / WL 的当前值显示、回车 / 应用、模板保存 / 删除 / 重启恢复均最多一位小数；整数不显示 `.0`。220 / 250 / 420 px 工具栏中输入框尺寸保持固定。
- 手册 / PACS / 设置切换复验：24 passed。修复切换期间播放状态为 undefined，以及日期弹窗父项销毁后的绑定警告。

## macOS 原生与打包检查

分别独立运行 `tests/test_local_import.py::test_native_volume_receives_file_drop[ct|pet|fusion]`，设置 `VOXENRA_NATIVE_QA=1 QT_QPA_PLATFORM=cocoa QT_QUICK_BACKEND=software`，3 个用例全部通过。真实 VTK 窗口收到 QDragEnterEvent / QDropEvent 后导入文件，原 3D 页签保持可用。

使用共享 `scripts/build_windows.py::pyinstaller_command` 的 `--collect-all` / `--copy-metadata` 参数，构建 macOS arm64 独立解码探针：JPEG Baseline、Extended、Lossless、JPEG-LS、JPEG 2000 参考文件全部成功解码，RLE / JPEG-LS / JPEG 2000 无损往返像素一致，7z 往返字节一致。此项验证动态解码器与入口点 metadata 随包收集，不等同于完成应用安装包发布。

Windows 原生拖拽与完整安装包验收仍需 Windows 真机执行；当前主机无法替代该项。RAR、加密及分卷包不在支持范围，多帧 / 彩色的完整阅片与体重建能力沿用既有边界，详见 [本地导入](../local-import.md)。

## 全量回归

```bash
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software PYTHONPATH=src:tests \
  python -m pytest -q --tb=short
```

按测试文件隔离进程运行全部 82 个测试文件（每个文件执行上述 pytest 命令，使用独立 basetemp），结果 **1120 passed、22 skipped、0 failed**，覆盖完整收集的 1142 项用例。22 项跳过需要原生窗口或指定环境；本次另外执行的 macOS 原生 CT / PET / 融合拖入 3 项全部通过。依赖锁定 `uv lock --check`、新增 Python 模块 Ruff F 类检查和 `git diff --check` 已通过。

常规单进程全量运行也已执行：两次分别发现工具栏播放状态、日历弹窗的 QML 生命周期警告，均已修复并专项复验。修复后的第三次单进程运行在最后一项 `test_image_and_volume_tab_transitions_keep_controller_types_separate` 发生一次原生 SIGSEGV，栈顶位于 Qt `QV4::QObjectWrapper::getProperty`；此前用例没有断言失败。该模块独立运行 4 项通过，按文件隔离全集同样通过。尚不能将这一单进程长时间运行崩溃判定为已修复，也未通过关闭 JIT 或跳过该用例隐藏问题。
