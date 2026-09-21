# -*- coding: utf-8 -*-
"""Unified Interactive portal launcher (self + share editions).

Self (default):  http://127.0.0.1:8766/?v=me
Share:           same server with ?v=share ; optional Cloudflare tunnel

Live WebUI stays on :8765 (SSH / separate tunnel). Portal only links to it.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import importlib.util
import json
import os
import re
import socketserver
import subprocess
import threading
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

OPT = Path(__file__).resolve().parent
DEMO = OPT.parent
PROJECT = DEMO.parent
STATUS = PROJECT / "DEMO_STATUS.txt"
CONFIG = PROJECT / "portal_config.json"
PORTAL_PAGE = f"{OPT.relative_to(PROJECT).as_posix()}/portal.html"
URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def build_manifest() -> dict:
    spec = importlib.util.spec_from_file_location(
        "_build_offline_manifest", OPT / "_build_offline_manifest.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    mod.main()
    return json.loads((PROJECT / "offline_manifest.json").read_text(encoding="utf-8"))


def find_cloudflared() -> Path | None:
    candidates = [
        Path(os.environ.get("USERPROFILE", "")) / "bin" / "cloudflared.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "cloudflared" / "cloudflared.exe",
        Path("C:/Program Files/cloudflared/cloudflared.exe"),
    ]
    for p in candidates:
        if p.exists():
            return p
    from shutil import which

    w = which("cloudflared")
    return Path(w) if w else None


def load_existing_config() -> dict:
    if not CONFIG.exists():
        return {}
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_portal_config(
    *,
    edition: str,
    stats: dict,
    live_share: str | None = None,
    live_me: str | None = None,
) -> dict:
    prev = load_existing_config()
    # Keep known-good remote Live URL across restarts (e.g. lhr.life / trycloudflare).
    share = (live_share or prev.get("live_url_share") or prev.get("live_url_fallback") or "").strip()
    me = (live_me or prev.get("live_url_me") or "http://127.0.0.1:8765/").strip()
    if not me:
        me = "http://127.0.0.1:8765/"
    cfg = {
        "edition": edition,
        "live_url_me": me,
        "live_url_share": share,
        "live_url_fallback": share or prev.get("live_url_fallback") or "",
        "offline_path": f"/{OPT.relative_to(PROJECT).as_posix()}/offline_orbit_viewer.html",
        "free_path": f"/{OPT.relative_to(PROJECT).as_posix()}/free_camera.html",
        "tech_path": f"/{OPT.relative_to(PROJECT).as_posix()}/tech_principles.html",
        "portal_path": f"/{PORTAL_PAGE}",
        "stats": stats,
        "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return cfg


def write_status(
    *,
    edition: str,
    local: str,
    stats: dict,
    public: str | None,
    live_share: str | None,
) -> None:
    me = f"{local}?v=me"
    share = f"{(public or local).rstrip('/')}/?v=share"
    lines = [
        "LagerNVS Interactive 最终版",
        f"updated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "【本地版】",
        f"  {me}",
        "  Live : http://127.0.0.1:8765/",
        f"  原理: {local.rstrip('/')}/{OPT.relative_to(PROJECT).as_posix()}/tech_principles.html",
        "",
        "【分享版】",
        f"  {share}",
        f"  Live 公网: {live_share or '未配置'}",
        "",
        f"样本: {stats.get('scenes', '?')} scenes | "
        f"{stats.get('hq_stills', '?')} HQ | "
        f"{stats.get('orbit_clips', '?')} orbit | "
        f"{stats.get('input_thumbs', '?')} inputs",
        "",
        "启动本地: python 07_交互式渲染演示/06_交互功能优化/start_portal.py",
        "启动分享: python 07_交互式渲染演示/06_交互功能优化/start_portal.py --share --tunnel",
        "",
    ]
    STATUS.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines), flush=True)


def tunnel_loop(port: int, label: str, on_url) -> None:
    exe = find_cloudflared()
    if not exe:
        print(f"[{label}] cloudflared missing", flush=True)
        return
    while True:
        cmd = [str(exe), "tunnel", "--url", f"http://127.0.0.1:{port}"]
        print(f"[{label}] start {' '.join(cmd)}", flush=True)
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as e:
            print(f"[{label}] {e}", flush=True)
            time.sleep(8)
            continue
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                print(f"[{label}] {line}", flush=True)
            m = URL_RE.search(line)
            if m:
                on_url(m.group(0) + "/")
        print(f"[{label}] exit {proc.wait()}; retry 5s", flush=True)
        on_url(None)
        time.sleep(5)


def probe_live_url(url: str, timeout: float = 6.0) -> bool:
    if not url:
        return False
    try:
        req = Request(url, headers={"User-Agent": "LagerNVS-portal-probe"})
        with urlopen(req, timeout=timeout) as r:
            if getattr(r, "status", 200) >= 400:
                return False
            body = r.read(6000).decode("utf-8", "replace")
            return any(
                k in body
                for k in ("LagerNVS", "interactive_viewer", "WebSocket", "canvas")
            )
    except Exception:
        return False


def pick_live_endpoint(cfg: dict) -> tuple[str, list[str]]:
    """Prefer local 8765, then configured public URLs. Probe in priority order."""
    candidates: list[str] = []
    local = "http://127.0.0.1:8765/"
    candidates.append(local)
    for k in ("live_url_share", "live_url_fallback", "live_url_cf", "live_url_me"):
        u = (cfg.get(k) or "").strip()
        if not u:
            continue
        if not u.endswith("/"):
            u += "/"
        if u not in candidates:
            candidates.append(u)
    for u in candidates:
        # Local: short timeout; remote: longer
        to = 2.5 if "127.0.0.1" in u or "localhost" in u else 7.0
        if probe_live_url(u, timeout=to):
            return u, candidates
    return "", candidates


class PortalHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT), **kwargs)

    def log_message(self, fmt: str, *args) -> None:  # quieter
        if args and str(args[0]).startswith("GET /api/"):
            return
        super().log_message(fmt, *args)

    def do_GET(self):  # noqa: N802
        if self.path.startswith("/api/live_status"):
            cfg = load_existing_config()
            chosen, checked = pick_live_endpoint(cfg)
            ws = ""
            if chosen:
                p = urlparse(chosen)
                ws = ("wss://" if p.scheme == "https" else "ws://") + p.netloc
            payload = {
                "ok": bool(chosen),
                "url": chosen,
                "ws": ws,
                "checked": checked,
                "hint": (
                    "ssh -L 8765:<GPU_IP>:8765 -N ustc-lager"
                    if not chosen
                    else ""
                ),
            }
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()


def main() -> None:
    parser = argparse.ArgumentParser(description="LagerNVS unified Interactive portal")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--share", action="store_true", help="default open share edition")
    parser.add_argument("--tunnel", action="store_true", help="Cloudflare for portal :8766")
    parser.add_argument(
        "--live-tunnel",
        action="store_true",
        help="also tunnel Live :8765 into portal_config.live_url_share",
    )
    parser.add_argument("--live-url", default="", help="manual Live public URL for share edition")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    manifest = build_manifest()
    stats = manifest.get("stats") or {}
    edition = "share" if args.share else "me"
    local = f"http://127.0.0.1:{args.port}/"
    prev_cfg = load_existing_config()
    seeded_live = (args.live_url or prev_cfg.get("live_url_share") or prev_cfg.get("live_url_fallback") or "").strip() or None
    public_holder: dict[str, str | None] = {"portal": None, "live": seeded_live}

    def refresh_cfg() -> None:
        write_portal_config(
            edition=edition,
            stats=stats,
            live_share=public_holder["live"],
            live_me="http://127.0.0.1:8765/",
        )
        write_status(
            edition=edition,
            local=local,
            stats=stats,
            public=public_holder["portal"],
            live_share=public_holder["live"],
        )

    refresh_cfg()

    if args.tunnel:
        def on_portal(url: str | None) -> None:
            public_holder["portal"] = url
            refresh_cfg()

        threading.Thread(
            target=tunnel_loop, args=(args.port, "portal-tunnel", on_portal), daemon=True
        ).start()

    if args.live_tunnel:
        def on_live(url: str | None) -> None:
            public_holder["live"] = url or (args.live_url or None)
            refresh_cfg()

        threading.Thread(
            target=tunnel_loop, args=(8765, "live-tunnel", on_live), daemon=True
        ).start()

    handler = PortalHandler
    socketserver.TCPServer.allow_reuse_address = True
    open_url = f"{local}?v={'share' if args.share else 'me'}"

    # Ensure root index points at portal
    index = PROJECT / "index.html"
    index.write_text(
        "<!DOCTYPE html><meta charset=utf-8>"
        f'<meta http-equiv=refresh content="0;url=/{PORTAL_PAGE}?v=me">'
        f'<a href="/{PORTAL_PAGE}?v=me">LagerNVS Interactive Hub</a>\n',
        encoding="utf-8",
    )

    with socketserver.ThreadingTCPServer(("127.0.0.1", args.port), handler) as httpd:
        httpd.daemon_threads = True
        print(f"Portal serving {PROJECT} → {open_url}", flush=True)
        if not args.no_open:
            webbrowser.open(open_url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped", flush=True)


if __name__ == "__main__":
    main()
