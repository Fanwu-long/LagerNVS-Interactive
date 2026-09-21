# -*- coding: utf-8 -*-
"""Double-click / one-command launcher for the final package."""
from pathlib import Path
import runpy

runpy.run_path(
    str(Path(__file__).resolve().parent / "07_交互式渲染演示" / "06_交互功能优化" / "start_portal.py"),
    run_name="__main__",
)
