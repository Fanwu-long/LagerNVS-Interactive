# -*- coding: utf-8 -*-
"""Wait for local Live :8765 then open viewers + update portal_config."""
from __future__ import annotations

import json
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CFG = ROOT / "portal_config.json"
STATUS = ROOT / "LIVE_STATUS.txt"


def alive(url: str, timeout: float = 2.5) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read(1500).decode("utf-8", "replace")
            return r.status == 200 and ("LagerNVS" in body or "canvas" in body)
    except Exception:
        return False


def main() -> None:
    local = "http://127.0.0.1:8765/"
    print("Waiting for SSH forward → http://127.0.0.1:8765/ ...", flush=True)
    for i in range(180):  # up to 6 min
        if alive(local):
            print("LIVE_LOCAL_OK", flush=True)
            cfg = {}
            if CFG.exists():
                try:
                    cfg = json.loads(CFG.read_text(encoding="utf-8"))
                except Exception:
                    cfg = {}
            cfg["live_url_me"] = local
            cfg["live_url_share"] = cfg.get("live_url_share") or ""
            cfg["live_url_fallback"] = cfg.get("live_url_fallback") or ""
            cfg["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
            cfg["ssh_forward"] = True
            CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
            STATUS.write_text(
                f"Live LOCAL OK via SSH\n{local}\nupdated: {cfg['updated']}\n"
                "Portal: http://127.0.0.1:8766/?v=me\n"
                "Free: http://127.0.0.1:8766/07_交互式渲染演示/06_交互功能优化/free_camera.html\n",
                encoding="utf-8",
            )
            webbrowser.open(local)
            webbrowser.open("http://127.0.0.1:8766/07_交互式渲染演示/06_交互功能优化/free_camera.html?live=1")
            webbrowser.open("http://127.0.0.1:8766/?v=me")
            return
        if i % 10 == 0:
            print(f"  still waiting... {i*2}s (complete 2FA in SSH window if prompted)", flush=True)
        time.sleep(2)
    print("TIMEOUT: SSH forward not up", flush=True)


if __name__ == "__main__":
    main()
