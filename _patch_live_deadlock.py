# -*- coding: utf-8 -*-
from pathlib import Path

p = Path("interactive_viewer.html")
t = p.read_text(encoding="utf-8")
if "window.__lastPoseSentAt" not in t and "if (!lastFrameDrawn) return;" in t:
    t = t.replace(
        "if (!lastFrameDrawn) return;",
        "const stuck=!lastFrameDrawn&&(performance.now()-(window.__lastPoseSentAt||0)>800); if(!lastFrameDrawn&&!stuck) return;",
    )
    t = t.replace(
        "lastFrameDrawn = false;\n  ws.send",
        "lastFrameDrawn=false; window.__lastPoseSentAt=performance.now();\n  ws.send",
    )
    p.write_text(t, encoding="utf-8")
    print("HTML_OK")
else:
    print("HTML_ALREADY_OR_MISS")

sp = Path("run_interactive_server.py")
s = sp.read_text(encoding="utf-8")
if "first frame flushed" not in s:
    old = "frame_count += 1\n                if frame_count % 30 == 0:"
    new = (
        "frame_count += 1\n"
        "                if frame_count == 1 and pending_jpeg is not None:\n"
        "                    jpeg_bytes = await pending_jpeg\n"
        "                    try:\n"
        "                        await websocket.send(pending_header + jpeg_bytes)\n"
        '                        print("  first frame flushed", flush=True)\n'
        "                    except websockets.ConnectionClosed:\n"
        "                        break\n"
        "                    pending_jpeg = None\n"
        "                    pending_header = None\n"
        "                if frame_count % 30 == 0:"
    )
    if old in s:
        sp.write_text(s.replace(old, new), encoding="utf-8")
        print("PY_OK")
    else:
        print("PY_MISS")
else:
    print("PY_ALREADY")
