# -*- coding: utf-8 -*-
"""Share edition — delegates to long-lived tunnel keeper."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "启动分享版_长驻.py"), run_name="__main__")
