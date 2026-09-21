# -*- coding: utf-8 -*-
"""Share launcher preferring localhost.run (usually opens in China).

trycloudflare often fails local/ISP DNS — not used as primary here.
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HUB = ROOT / "07_交互式渲染演示" / "06_交互功能优化"
SHARE_URL = ROOT / "SHARE_URL.txt"
PID_FILE = ROOT / "ssh_tunnel.pid"

URL_RE = re.compile(
    r"https?://[a-zA-Z0-9-]+\.(?:lhr\.life|localhost\.run|serveo\.net|pinggy\.link)(?:/[^\s]*)?"
)


def bad(u: str) -> bool:
    u = u.lower()
    return any(x in u for x in ("admin.localhost.run", "dashboard", "docs."))


def write_share(url: str, backend: str) -> None:
    share = url if "?v=" in url else url.rstrip("/") + "/?v=share"
    SHARE_URL.write_text(
        f"LagerNVS 分享链接（{backend}）\n{share}\n\n"
        f"更新: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        "保持本机开机、勿休眠；不要结束本脚本/ssh 进程。\n",
        encoding="utf-8",
    )
    print(f"[share] {share}", flush=True)


def ensure_portal() -> subprocess.Popen:
    cmd = [
        sys.executable,
        str(HUB / "start_portal.py"),
        "--share",
        "--no-open",
        "--port",
        "8766",
    ]
    print("[portal]", " ".join(cmd), flush=True)
    return subprocess.Popen(cmd, cwd=str(ROOT))


def open_tunnel() -> tuple[subprocess.Popen, str, str]:
    attempts = [
        (
            [
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=NUL",
                "-o",
                "ServerAliveInterval=30",
                "-R",
                "80:127.0.0.1:8766",
                "nokey@localhost.run",
            ],
            "localhost.run",
        ),
        (
            [
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=NUL",
                "-o",
                "ServerAliveInterval=30",
                "-R",
                "80:127.0.0.1:8766",
                "serveo.net",
            ],
            "serveo",
        ),
    ]
    for cmd, name in attempts:
        print("[tunnel] try", name, flush=True)
        p = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        t0 = time.time()
        url = None
        assert p.stdout is not None
        while time.time() - t0 < 50:
            line = p.stdout.readline()
            if not line:
                if p.poll() is not None:
                    break
                time.sleep(0.1)
                continue
            line = line.rstrip()
            print("[tunnel]", line, flush=True)
            for m in URL_RE.finditer(line):
                cand = m.group(0).rstrip("/.,)")
                if not bad(cand):
                    url = cand
                    break
            if url:
                break
        if url:
            PID_FILE.write_text(str(p.pid), encoding="utf-8")
            return p, url, name
        try:
            p.kill()
        except OSError:
            pass
    raise SystemExit("无法建立公网隧道（localhost.run / serveo 均失败）")


def main() -> None:
    portal = ensure_portal()
    time.sleep(2)
    tunnel, url, backend = open_tunnel()
    write_share(url, backend)
    try:
        while True:
            if portal.poll() is not None:
                print("[portal] exited", portal.returncode, flush=True)
                break
            if tunnel.poll() is not None:
                print("[tunnel] exited; restarting…", flush=True)
                tunnel, url, backend = open_tunnel()
                write_share(url, backend)
            time.sleep(3)
    except KeyboardInterrupt:
        print("stopped", flush=True)
    finally:
        for p in (tunnel, portal):
            try:
                p.terminate()
            except Exception:
                pass


if __name__ == "__main__":
    main()
