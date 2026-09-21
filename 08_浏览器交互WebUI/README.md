# Live GPU WebUI（汇报加分项）

本目录用于平台上启动 **真·自由视角** 实时渲染。

日常离线汇报请用上级目录：`python 启动本地版.py`

## 快速

1. 同步 `01_官方Browser_Viewer代码/` 与 `03_示例场景_test_data/` 到平台 `~/lagernvs`
2. `sbatch 02_平台启动脚本/01_run_webui_live.sbatch`
3. 本机：`ssh -L 8765:<GPU_IP>:8765 …`
4. 打开门户自由视角 →「真·自由视角」

详见 `04_说明文档/README_快速启动.md`
