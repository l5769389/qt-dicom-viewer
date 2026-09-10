# 0.4.0 文件／文件夹压缩导入修正

本次按用户纠正，将压缩支持定位为文件和文件夹归档。撤回 `f9301bb` 新增的 DICOM 像素解码依赖、缩略图兼容分支及相关测试／宣传说明，保留此前拖拽导入和最多一位小数的窗值输入。版本仍为尚未发布的 0.4.0。

## 实现与范围

- RAR4、RAR5、固实压缩，支持包含中文路径和多层目录的归档。既有 ZIP、7z、TAR 与单文件 GZ／BZ2／XZ 继续可用。
- `unrar2-cffi==0.5.0` 随应用提供原生 UnRAR 7.21.0。采用 TEST 回调流式接收解压字节并验证 CRC；原生库不负责写入文件，输出统一经过现有路径、文件数、单文件和总字节限制。RAR 字典上限 512 MiB。
- 回调捕获取消与限额错误，在原生调用退出后重新抛出；失败回滚仅清理本次缓存，保留已有视图的数据。
- 加密包和分卷包显示具体提示，需先解密、合并解压。源压缩包和原始 DICOM 保持不变。
- PyInstaller 收集 `unrar`、`py7zr`、`_cffi_backend`、封装库 metadata 与 `licenses/`。macOS 和 Windows 使用相同参数。

## 验证环境与结果

macOS Apple Silicon，干净的临时环境由修改后的 `uv.lock` 安装：Python 3.13.14、PySide6 6.11.1、pydicom 3.0.2、VTK 9.5.2。环境未安装此次撤回的 pylibjpeg、libjpeg、OpenJPEG、RLE 和 pyjpegls 依赖。

- RAR 专项：**22 passed**。真实压缩 RAR4、RAR5、固实压缩文件逐字节匹配独立预期；CRC 损坏、截断数据、加密、分卷、路径越界、链接／特殊文件、大小写文件名冲突、字典／文件数／解压体积上限、原生回调期间取消、嵌套及无后缀识别。参考文件来源和许可见 [fixtures](../../tests/fixtures/rar/README.md)。
- 导入与真实 QML：**31 passed、3 skipped**。包含文件、文件夹、RAR／ZIP／7z 拖入、后台完成后打开视图、清空列表后保留视图、复制语义及中文 DICOM 路径。没有 QML 绑定或布局警告。
- macOS 原生 CT、PET、融合 3D：分别在独立进程执行 RAR 拖入，共 **3 passed**；原有 3D 画面和页签保持可用。
- 冻结程序：使用共享打包配置的归档依赖收集参数构建 macOS arm64 独立探针。清除 `PYTHONPATH`／`VIRTUAL_ENV` 并设置 `PATH=/nonexistent` 后，RAR4、RAR5、固实 RAR5、ZIP、7z 均成功解包并校验内容，随包许可证存在。无需外部 WinRAR／unrar 命令。此项不是完整安装包发布；Windows 原生拖拽和安装包仍需 Windows 主机验收。
- 完整测试集按文件隔离进程执行 **82 个测试文件：1133 passed、22 skipped、0 failed**。逐文件结果见 [JSON](rar-import-correction-results.json)。跳过项需要特定环境，原生拖入三项已另行验证。既有数值计算／第三方弃用警告不在此次修正范围。
- `uv lock --check`、新增 Python 模块 Ruff F 检查和 `git diff --check` 通过。

回归命令：

```sh
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software PYTHONPATH=src:tests \
  python -m pytest tests/test_rar_import.py tests/test_local_import.py -q --tb=short

VOXENRA_NATIVE_QA=1 QT_QPA_PLATFORM=cocoa QT_QUICK_BACKEND=software PYTHONPATH=src:tests \
  python -m pytest 'tests/test_local_import.py::test_native_volume_receives_file_drop[ct]' -q
```

全集使用每个 `tests/test_*.py` 单独运行 pytest 和独立 basetemp，未跳过任何测试文件。此前单进程长时间运行在 Qt `QV4::QObjectWrapper::getProperty` 发生的崩溃记录仍保留在 [上一轮验证](compressed-import.md)；本次未改动该路径，不声称已修复该历史问题。
