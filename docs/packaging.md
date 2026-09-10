# Voxenra 打包与安装

## 输出与安装界面

| 平台 | 本机构建入口 | 产物 / 安装方式 |
| --- | --- | --- |
| macOS | `bash scripts/build_macos.sh` | `dist/macos/Voxenra.app`；`dist/installers/Voxenra-<版本>-macos-<架构>.dmg`，打开后将应用拖入 Applications |
| Windows x64 | `./scripts/build_windows.ps1` | `dist/installers/Voxenra-<版本>-windows-x64-setup.exe`，原生安装向导 |
| Windows x64 便携版 | `scripts\build_windows.bat` | `dist/Voxenra.exe`，保留原有入口，无安装向导 |

脚本可以从任意工作目录调用。需要完整源码、uv，以及首次构建时的网络访问。
使用锁定的 Python 3.13 依赖，分别创建 `.venv-build-macos` / `.venv-build-windows`，不修改开发虚拟环境。
品牌源文件为 `voxenra-mark.svg`，随应用提供 1024 像素 PNG，并导出 ICO / ICNS；ICO 包含 16～256 像素表示，ICNS 包含最高 1024 像素的 Retina 表示。Windows 便携版、安装版与安装器均嵌入图标；开始菜单和桌面快捷方式与运行进程使用同一 AppUserModelID。Qt 窗口和 macOS Dock 使用同一品牌图标，macOS 应用包会检查 Info.plist 引用的 ICNS 存在。所有 QML、导航及操作图标随应用收集。
只收集源码和依赖，不收集本地 DICOM 文件。产物包含 Python、Qt、VTK；解码器能力仍由项目依赖决定。

## macOS

在目标架构的 Mac 上执行：

```bash
bash scripts/build_macos.sh
# 仅生成应用：
bash scripts/build_macos.sh --app-only
```

脚本使用当前 Python 的 arm64 / x86_64 架构，不宣称生成通用二进制。
DMG 使用 Finder 原生安装窗口，固定排列应用、Applications 链接和中英文安装说明。
安装时拖拽应用，完成后推出磁盘映像；更新前退出旧版本。
卸载时从 Applications 将应用移到废纸篓，不主动清理个人影像或日志。
脚本检查应用存在、更新 bundle 版本、校验签名，并验证 DMG 完整性。

默认使用 ad-hoc 测试签名，这不等于 Apple 信任认证。公开分发需要自己的 Developer ID Application 证书和公证配置：

```bash
bash scripts/build_macos.sh \
  --sign-identity 'Developer ID Application: YOUR NAME (TEAMID)' \
  --notary-profile 'your-saved-notarytool-profile'
```

也可使用 `MACOS_SIGN_IDENTITY` / `MACOS_NOTARY_PROFILE` 环境变量。
公证配置需提前通过 Apple 的 `notarytool` 保存到钥匙串；不要将证书密码或 Apple 凭据提交到仓库。
只有显式提供公证配置时才会提交文件到 Apple。公证成功后装订并验证票据。
未签名或未公证包可能触发 Gatekeeper；不要全局关闭系统安全检查。

## Windows

在 Windows x64 安装 uv 和 [Inno Setup 6.6+](https://jrsoftware.org/isinfo.php)，然后执行：

```powershell
./scripts/build_windows.ps1
# 自定义编译器位置（含空格路径受支持）：
./scripts/build_windows.ps1 -IsccPath 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
```

也可设置 `INNO_SETUP_COMPILER`。脚本先检查编译器，再冻结应用并编译安装器。
PowerShell 若被组织执行策略阻止，请按组织策略允许脚本，或通过 uv 直接运行 Python 入口；无需关闭系统安全策略。

安装向导提供中英文选择、欢迎页、安装说明、路径、可选桌面快捷方式、安装进度与完成后启动。
窗口使用原生现代样式，并随系统选择深浅色；复用 Voxenra 品牌图标。
中文覆盖主要安装/卸载流程，底层技术错误保留 Inno Setup 英文回退。
默认安装到 `%LOCALAPPDATA%\Programs\Voxenra`，仅当前用户，无管理员权限要求。
开始菜单会添加快捷方式；桌面快捷方式默认不选。
固定 AppId 用于同一应用的升级识别；版本统一读取 `pyproject.toml`。
卸载入口在 Windows“设置 → 已安装的应用”。卸载不执行通配目录清理；个人 DICOM 文件请保存在安装目录之外。

默认 EXE 未做 Authenticode 签名，可能出现 SmartScreen / 未知发布者提示。
公开发布需使用自己的证书完成应用 EXE 与最终安装器的签名，并在干净目标机验收；此脚本不会猜测或导入证书。

## GitHub Actions

**Build Windows packages** 在 `main` 的 `src/`、`scripts/`、`packaging/`、`tests/`、依赖文件或该工作流更新后自动触发。执行回归后生成便携 EXE、安装向导 EXE 及 SHA-256 校验文件，上传到该次运行的 Artifacts。仅修改文档不会启动构建；同一分支的新构建会取消未完成的旧构建。

推送 `v*` 版本标签后，会构建该标签源码；标签必须与 `pyproject.toml` 中的版本一致（例如 `v0.2.0` 对应 `0.2.0`）。测试与图标校验成功后，独立发布任务下载本次 Artifact，再校验 SHA-256，并将以下四个附件上传到同名 Release：

- `Voxenra-<版本>-windows-x64-portable.exe` 与 `.exe.sha256`
- `Voxenra-<版本>-windows-x64-setup.exe` 与 `.exe.sha256`

已有 Release 保留说明、macOS 附件和发布状态；没有时先创建草稿，便于与 macOS 包一并发布。重跑只更新对应版本的 Windows 附件。Release Assets 不受 Actions Artifact 的 14 天保留期影响。

也可在手动运行时填写 `release_tag` 补建已有标签；工作流会检出该标签源码，而不是把当前 main 的产物放进旧版本。留空时保持普通构建。控制台诊断选项只生成诊断便携 EXE，禁止与 Release 发布组合使用。构建任务维持只读权限，只有发布任务获得 `contents: write`。**Build native installers** 保留为双平台手动入口。

若已有测试通过的构建，可同时填写 `release_tag` 和 `artifact_run_id`，直接在 GitHub runner 上归档已有产物，不重复打包。发布任务会核验来源是本仓库的成功 Windows 工作流，且构建提交与版本标签完全一致；版本号或 SHA-256 不符、Artifact 过期时均停止上传。
macOS 架构随 runner 而定，以产物文件名为准；Intel 包可在 Intel Mac 本机构建。
CI 默认也是测试签名/未签名产物；Windows CI 安装当前 Inno Setup 版本，因此编译器版本不由 uv.lock 锁定。

应用现名 Voxenra，macOS bundle ID 与 Windows AppUserModelID 统一为 `com.junliu.voxenra`，Qt 的组织名及应用名均为 Voxenra，日志为 `voxenra.log`。安装器 AppId 保持不变以支持原安装升级；安装向导默认使用 `%LOCALAPPDATA%\Programs\Voxenra`，不再从注册表沿用旧品牌目录，仍可在目录页或 `/DIR` 指定自定义位置。升级时刷新安装器管理的 `_internal\PySide6` 运行库，防止已精简的 Qt 插件残留；清理安装目标内的旧品牌可执行文件和旧快捷方式，启动时复制旧版配置且不覆盖新配置。旧影像与日志不移动或删除。旧名称只在配置迁移、安装升级清理及历史构建记录中保留。Qt 工程与资源清单分别为 `Voxenra.qmlproject`、`Voxenra.qrc`。

## 验收清单

### Voxenra 0.2.0（2026-09-08）

版本标签 `v0.2.0` 指向提交 `8748f2f`；macOS 构建源码与标签中的应用、打包脚本、资源及依赖文件完全一致。

- macOS arm64：完整回归 870 通过、15 跳过。Voxenra.app 和 223 MiB DMG 已构建；系统图标、新名称、0.2.0 版本、Retina 图标及签名完整性检查通过。只读挂载检查安装内容后推出；冻结应用运行 12 秒，无 Python 异常或 QML 加载失败。
- 真实 Qt/QML 窗口验证 2D、MPR、4D、CT 3D、PET/CT 融合及融合 3D，并保存六张 README 截图；无 QML 警告。使用本地匿名化 DICOM 副本，PET SUV 换算比例与原数据一致；未提交原始影像。
- Windows x64：[标签自动构建及 Release 上传](https://github.com/l5769389/qt-dicom-viewer/actions/runs/34192544207)成功，完整回归 870 通过、15 跳过。便携 EXE 与安装版应用的 7 个 PE 图标尺寸均与新品牌 ICO 逐字节一致。
- [Voxenra v0.2.0](https://github.com/l5769389/qt-dicom-viewer/releases/tag/v0.2.0)提供 macOS arm64 DMG、Windows x64 便携版及安装器；三个包及各自 SHA-256 共 6 个附件，GitHub 摘要与校验文件一致。macOS DMG 约 223 MiB，Windows 便携版约 221 MiB、安装器约 149 MiB。
- 两个工作流通过 actionlint；README 图片链接、QRC 资源及依赖锁文件一致性检查通过。
- Windows CI 改用 Qt 软件渲染执行离屏 QML 测试。首次尝试出现一次标签页 incubation 警告，下一次未复现该警告但 PET 首次加载超过 3 秒；现将首次体积加载与定位计时分开，加载等待 10 秒，拖动反馈第 95 百分位低于 33 ms 的断言保留。调整后 Windows 完整回归通过；本地标签 QML 连续 12 轮（60 项）及针对性回归 25 项通过。

### DICOMVision 0.1.0 历史验证

验证日期 2026-09-08，版本提交 `d8ae41b`：

- macOS arm64：完整回归 870 通过、15 跳过；生成 0.1.0 的 `.app` 和约 224 MiB 的 DMG。系统图标读取显示正确 DV 图标；bundle 的 ICNS 引用、Retina 图标、签名完整性与 DMG 完整性检查通过。只读挂载检查应用、安装说明与 Applications 链接后推出。冻结应用离屏运行 12 秒，无 Python 异常、图标错误或 QML 加载失败。
- Windows x64：[main 推送自动构建](https://github.com/l5769389/qt-dicom-viewer/actions/runs/34181423224)成功，完整回归 870 通过、15 跳过；便携 EXE 和 Inno Setup 安装包生成成功。读取便携版及安装版应用的 PE 图标资源，7 个尺寸均与品牌 ICO 逐字节一致。两个 EXE 及 SHA-256 文件已上传为 `DICOMVision-windows-x64` Artifact。
- [v0.1.0 预发布](https://github.com/l5769389/qt-dicom-viewer/releases/tag/v0.1.0)已归档 macOS arm64 DMG、Windows x64 便携 EXE、安装向导 EXE 及各自 SHA-256，共 6 个附件；Windows 已通过 [Release 发布任务](https://github.com/l5769389/qt-dicom-viewer/actions/runs/34187595978)从原成功构建直接转存，构建提交与标签一致，GitHub 附件摘要与校验值一致。
- Release 工作流通过 actionlint；版本不匹配、诊断版发布、摘要损坏、来源提交不一致、失败构建及其他工作流来源均有拒绝上传验证。新增标签构建配置的 [main 回归](https://github.com/l5769389/qt-dicom-viewer/actions/runs/34186709427)也已全部通过；日常 main 构建不会发布 Release。

跳过项为需要外部 PACS / Docker 环境的测试。上述检查不等同于干净目标机的安装、升级、卸载或真实影像渲染验收；Windows 快捷方式的桌面视觉效果、Intel Mac 与商业签名 / 公证流程尚未实测。

构建成功不代表目标机验证完成。每个准备发布的 OS / 架构都应单独验证：

1. 没有额外 Python / Qt 的机器上安装并启动；中文、空格路径正常。
2. 导航与操作图标、QML 面板完整；打开测试 DICOM 并检查 2D、MPR、3D、Tag。
3. 重复安装/升级前正确退出旧应用；快捷方式和版本信息正确。
4. 卸载后个人 DICOM 文件与日志保留；无额外注册表或安全设置修改。
5. 正式签名包通过目标系统信任检查。

PyInstaller 必须在目标 OS 上构建，参见 [PyInstaller 使用文档](https://www.pyinstaller.org/en/stable/usage.html)。
原生安装窗口分别参考 [dmgbuild 设置](https://dmgbuild.readthedocs.io/en/latest/settings.html) 和
[Inno Setup WizardStyle](https://jrsoftware.org/ishelp/topic_setup_wizardstyle.htm)。
运行图标与任务栏标识分别采用 [Qt 应用图标 API](https://doc.qt.io/qt-6/qguiapplication.html#windowIcon-prop) 和 [Windows AppUserModelID](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-setcurrentprocessexplicitappusermodelid)。

## 0.4.0 压缩导入依赖

构建环境通过锁定的 `uv.lock` 安装 py7zr 和 unrar2-cffi 0.5.0。后者包含原生 UnRAR 库，用户无需安装 WinRAR 或外部 unrar 命令。支持的 Python 范围为 3.11–3.14，正式构建继续使用 Python 3.13。

共享 PyInstaller 命令使用 `--collect-all py7zr`、`--collect-all unrar`、`--hidden-import _cffi_backend` 和 `--copy-metadata unrar2-cffi`，macOS、Windows 共用这些收集参数；`licenses/` 中的 UnRAR 与封装库许可也随包收集。不能只复制 Python 文件而遗漏原生库。

打包验证需在不依赖外部解包命令的环境中，实际导入 RAR4、RAR5 固实压缩、ZIP 与 7z；RAR 只在私有临时目录中输出经路径检查的文件。新增压缩支持针对文件／文件夹归档，不额外安装 DICOM 像素解码器。


## 依赖体积优化

Windows 与 macOS 共用 `packaging/hooks` 中的资源筛选：

- QML 依赖分析前移除未使用的 WebEngine、Qt Quick 3D、Qt 3D 桥接、PDF 视图和触屏虚拟键盘；保留全部 Controls 风格及桌面输入、JPEG / SVG 等图像插件。
- 应用资源保留全部 QML、JS、SVG、品牌图标和许可文件；已经被 SVG 替换的旧 PNG 图标原稿保留在仓库中，不进入安装包。
- VTK 三维绘制和 RAR / 7z 原生解包库保留。不使用 UPX 压缩 Qt DLL；macOS 调试符号裁剪实测几乎没有节省，未启用该选项。

macOS DMG 改用 [ULMO / LZMA](https://dmgbuild.readthedocs.io/en/latest/settings.html) 压缩，要求 macOS 10.15+，低于本项目当前 Qt 运行时的系统要求。Windows 安装器改为 [LZMA2 / ultra64](https://jrsoftware.org/ishelp/topic_setup_compression.htm) 整体压缩，独立压缩进程约需 742 MiB 内存，安装解压字典约需 64 MiB；换取更小的下载包，构建时间会增加。

本机 arm64 实测如下。安装内容按应用包内非符号链接文件的字节总和计算，DMG 为实际文件大小：

| 阶段 | 安装内容 | DMG |
| --- | --- | --- |
| 已发布 v1.0.0 | 655.9 MiB | 227.2 MiB |
| 第一轮精简 | 401.3 MiB | 129.4 MiB |
| 第二轮资源精简及更强压缩 | 376.3 MiB | 71.9 MiB |

第二轮安装内容再减少约 6.2%，下载包再减少约 44.4%。LZMA DMG 已通过只读挂载、2,590 个文件的逐项 SHA-256 比对及完整签名检查。Windows 实际节省量仍需以 Windows 构建产物为准。

macOS 冻结验证已覆盖 ZIP / RAR / 7z 混合导入、CT 2D、PET MPR、CT / PET 原生 3D 截图、三维画面上的独立导入错误窗口、设置和操作手册；无 QML 警告。进度窗口的长中文、长英文路径、六位数文件计数和状态切换，均已验证窗口尺寸及底部按钮位置稳定。

新包不会自动重命名电脑上已经存在的旧品牌文件夹；选择新安装位置时也不会搬动或清理旧目录中的用户文件。安装器的私有 Qt 运行库更新不涉及影像、用户设置和日志。Windows 新安装、旧品牌升级及空间回收仍需在下一次 Windows 构建后实测。
