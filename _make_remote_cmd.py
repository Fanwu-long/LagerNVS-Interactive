import base64, pathlib
root = pathlib.Path(r"d:\新建文件夹\LagerNVS-Interactive最终版")
src = root / "_patch_live_deadlock.py"
b64 = base64.b64encode(src.read_bytes()).decode("ascii")
cmd = (
    "cd ~/lagernvs; python -c \"import base64; open('/tmp/patch_live_deadlock.py','wb')"
    f".write(base64.b64decode('{b64}'))\"; python /tmp/patch_live_deadlock.py; "
    "grep -n 'first frame flushed\\|__lastPoseSentAt' run_interactive_server.py interactive_viewer.html | head; "
    "echo PATCHDONE\n"
)
(root / "_remote_patch_cmd.txt").write_text(cmd, encoding="utf-8")
print("ok", len(cmd))
