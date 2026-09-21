# Live 与 Offline 对比

| | A Live | B Offline |
|---|---|---|
| 入口 | 门户卡片 A → :8765 | 门户卡片 B → 同站 Offline 页 |
| 原理 | LagerNVS 按位姿当场渲染 | 同一模型结果预烘焙后交互 |
| 算力 | 需要 GPU | 不需要 |
| 画质 | 受实时分辨率与网络影响 | HQ 静帧更清晰 |
| 适用 | 证明实时新视角 | 讲解、无 GPU 演示 |

技术细节见：`07_交互式渲染演示/06_交互功能优化/tech_principles.html`
