import time, urllib.request, webbrowser, subprocess, sys
for i in range(120):
    try:
        r=urllib.request.urlopen('http://127.0.0.1:8765/', timeout=2)
        if r.status==200:
            webbrowser.open('http://127.0.0.1:8765/')
            webbrowser.open('http://127.0.0.1:8766/07_交互式渲染演示/06_交互功能优化/free_camera.html')
            print('LIVE_LOCAL_OK')
            sys.exit(0)
    except Exception:
        pass
    time.sleep(2)
print('TIMEOUT')
sys.exit(1)
