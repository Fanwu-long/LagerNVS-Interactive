import subprocess, re, time, pathlib, sys
root = pathlib.Path(r"d:\新建文件夹\LagerNVS-Interactive最终版")

def bad(u: str) -> bool:
    u = u.lower()
    return any(x in u for x in ("admin.localhost.run", "dashboard", "docs.", "github.com", "cloudflare.com"))

attempts = [
  (["ssh","-o","StrictHostKeyChecking=no","-o","UserKnownHostsFile=NUL","-o","ServerAliveInterval=30",
    "-R","80:127.0.0.1:8766","nokey@localhost.run"], "localhost.run"),
  (["ssh","-o","StrictHostKeyChecking=no","-o","UserKnownHostsFile=NUL","-o","ServerAliveInterval=30",
    "-R","80:127.0.0.1:8766","serveo.net"], "serveo"),
  (["ssh","-o","StrictHostKeyChecking=no","-o","UserKnownHostsFile=NUL","-o","ServerAliveInterval=30",
    "-p","443","-R","0:127.0.0.1:8766","a.pinggy.io"], "pinggy"),
]
pat = re.compile(r"https?://[a-zA-Z0-9-]+\.(?:localhost\.run|lhr\.life|serveo\.net|pinggy\.link|pinggy\.io)(?:/[^\s]*)?")

for cmd, name in attempts:
    print("TRY", name, flush=True)
    p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    t0=time.time(); url=None
    while time.time()-t0 < 50:
        line=p.stdout.readline()
        if not line:
            if p.poll() is not None: break
            time.sleep(0.1); continue
        line=line.rstrip()
        print(line, flush=True)
        for m in pat.finditer(line):
            cand=m.group(0).rstrip("/.,)")
            if not bad(cand):
                url=cand
                break
        if url: break
    if url:
        (root/"ssh_tunnel.pid").write_text(str(p.pid), encoding="utf-8")
        # keep child alive by not killing; detach note: when this script exits ssh may get SIGHUP on windows?
        # Start a keeper
        share = url if "?v=" in url else (url.rstrip("/") + "/?v=share")
        (root/"SHARE_URL.txt").write_text(
            f"LagerNVS 分享链接（{name}）\n{share}\n\n更新: {time.strftime('%Y-%m-%d %H:%M:%S')}\n本机勿休眠；SSH 隧道进程需保持运行。\n",
            encoding="utf-8")
        print("SHARE", share, flush=True)
        # Wait forever so ssh stays as child... actually Popen child survives on Windows after parent exit usually
        time.sleep(2)
        sys.exit(0)
    try: p.kill()
    except Exception: pass
    print("FAIL", name, flush=True)
sys.exit(1)
