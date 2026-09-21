# 维护脚本说明

日常汇报**不必**进这里。需要重建资源时：

| 脚本位置 | 作用 |
|---|---|
| `07_交互式渲染演示/06_交互功能优化/_build_offline_manifest.py` | 按清晰度重写 `offline_manifest.json` |
| `07_交互式渲染演示/06_交互功能优化/make_hq_orbits_from_stills.py` | HQ 静帧 → orbit（需 showcase 或 Pred） |
| `07_交互式渲染演示/06_交互功能优化/start_portal.py` | 正式启动器（`启动本地版.py` 会调用） |

重建示例：

```bash
python 07_交互式渲染演示/06_交互功能优化/_build_offline_manifest.py
python 启动本地版.py
```

未选用的软糊视频在 `../99_未选用素材/`，默认不进入演示列表。
