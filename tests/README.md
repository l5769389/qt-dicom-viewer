# 测试与验证

`test_*.py` 为 pytest 回归用例，`qml/` 为测试使用的 QML 场景。`manual/` 存放需显式运行的桌面检查、性能基准和 PACS 联调工具，不随普通 pytest 自动运行。所有命令均从项目根目录执行。

```sh
uv run --group dev pytest -q
```

## 桌面与性能检查

以下命令需要桌面会话；3D 检查还需要原生 OpenGL。使用合成数据，截图和基准输出放在临时目录。

```sh
uv run python tests/manual/smoke_3d.py /tmp/volume.png
uv run python tests/manual/smoke_pet_3d.py /tmp/pet-3d
uv run python tests/manual/smoke_water_qa.py /tmp/water-qa.png
uv run python tests/manual/benchmark_pet_locator.py /tmp/pet-locator.json
```

PET 基准使用接近实际规模的体积，需要足够内存。各项验收范围见 [三维编辑](../docs/volume-editing.md)、[PET 验证](../docs/validation/pet-fusion-workflow/README.md)和[水模 QA](../docs/water-qa.md)。

Windows 构建完成后，`manual/verify_windows_icons.py --icon <ICO> <EXE...>` 逐帧检查 PE 图标资源与品牌 ICO 一致，需要 build 依赖组；Windows 自动打包工作流会执行此检查。

## PACS 联调

入口为 `uv run python tests/manual/pacs_lab.py --help`。工具仍使用 `docker/pacs/` 下的 Compose、配置和产物目录，迁移不改变已有实验环境。启动服务及选择性运行端到端用例的步骤见 [PACS 联调说明](../docs/pacs-lab.md)。

## 专项分析与产物

一次性分析脚本与报告放在对应的 `docs/validation/<主题>/` 目录，额外科研依赖和原始数据要求由该报告说明，不加入应用运行依赖。例如本地 `spiral-mtf-slice11/` 中的 MTF 分析脚本与报告配套使用。

新增 pytest 用例放在本目录；新增手动验收工具放在 `manual/`；生成的临时图片、日志和缓存不放进 `scripts/`。`scripts/` 仅维护打包入口。

Windows 发布回归使用 `uv run --group dev python tests/run_isolated.py`，逐文件启动独立 pytest 进程，保留全部用例。每个文件的输出、JUnit XML 与汇总写入 `build/test-results/`，失败或超时阻止打包；Actions 同时归档这些诊断资料。可传入测试文件路径执行局部复查。
