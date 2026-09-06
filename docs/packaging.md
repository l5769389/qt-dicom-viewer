# DICOMVision 打包与安装

## 输出与安装界面

| 平台 | 本机构建入口 | 产物 / 安装方式 |
| --- | --- | --- |
| macOS | `bash scripts/build_macos.sh` | `dist/macos/DICOMVision.app`；`dist/installers/DICOMVision-<版本>-macos-<架构>.dmg`，打开后将应用拖入 Applications |
| Windows x64 | `./scripts/build_windows.ps1` | `dist/installers/DICOMVision-<版本>-windows-x64-setup.exe`，原生安装向导 |
| Windows x64 便携版 | `scripts\build_windows.bat` | `dist/DICOMVision.exe`，保留原有入口，无安装向导 |

脚本可以从任意工作目录调用。需要完整源码、uv，以及首次构建时的网络访问。
使用锁定的 Python 3.13 依赖，分别创建 `.venv-build-macos` / `.venv-build-windows`，不修改开发虚拟环境。
图标由现有品牌 PNG 导出 ICO / ICNS；所有 QML、导航及操作图标随应用收集。
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
窗口使用原生现代样式，并随系统选择深浅色；复用 DICOMVision 品牌图标。
中文覆盖主要安装/卸载流程，底层技术错误保留 Inno Setup 英文回退。
默认安装到 `%LOCALAPPDATA%\Programs\DICOMVision`，仅当前用户，无管理员权限要求。
开始菜单会添加快捷方式；桌面快捷方式默认不选。
固定 AppId 用于同一应用的升级识别；版本统一读取 `pyproject.toml`。
卸载入口在 Windows“设置 → 已安装的应用”。卸载不执行通配目录清理；个人 DICOM 文件请保存在安装目录之外。

默认 EXE 未做 Authenticode 签名，可能出现 SmartScreen / 未知发布者提示。
公开发布需使用自己的证书完成应用 EXE 与最终安装器的签名，并在干净目标机验收；此脚本不会猜测或导入证书。

## GitHub Actions

保留原有 **Build Windows EXE** 便携版工作流，新增 **Build native installers**，只允许手动触发。
后者分别使用 macOS 和 Windows runner，测试后上传安装包，不创建 Release、不自动发布。
macOS 架构随 runner 而定，以产物文件名为准；Intel 包可在 Intel Mac 本机构建。
CI 默认也是测试签名/未签名产物；Windows CI 安装当前 Inno Setup 版本，因此编译器版本不由 uv.lock 锁定。

## 验收清单

本次本地验证（2026-09-06，macOS arm64）：448 项测试通过；成功生成 0.1.0 的 `.app` 和约 223 MiB 的 DMG；
应用签名完整性、DMG 校验和通过。已只读挂载并检查 Finder 图标、拖拽箭头、安装说明与 Applications 链接，随后推出。
打包应用离屏运行 10 秒，无 Python 异常或 QML 加载失败；这不等同于真实影像渲染验收。
Windows 安装器仅做脚本/配置回归检查，尚未在 Windows 编译或执行安装、升级、卸载；Intel Mac 与商业签名/公证流程也未实测。

构建成功不代表目标机验证完成。每个准备发布的 OS / 架构都应单独验证：

1. 没有额外 Python / Qt 的机器上安装并启动；中文、空格路径正常。
2. 导航与操作图标、QML 面板完整；打开测试 DICOM 并检查 2D、MPR、3D、Tag。
3. 重复安装/升级前正确退出旧应用；快捷方式和版本信息正确。
4. 卸载后个人 DICOM 文件与日志保留；无额外注册表或安全设置修改。
5. 正式签名包通过目标系统信任检查。

PyInstaller 必须在目标 OS 上构建，参见 [PyInstaller 使用文档](https://www.pyinstaller.org/en/stable/usage.html)。
原生安装窗口分别参考 [dmgbuild 设置](https://dmgbuild.readthedocs.io/en/latest/settings.html) 和
[Inno Setup WizardStyle](https://jrsoftware.org/ishelp/topic_setup_wizardstyle.htm)。
