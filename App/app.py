import subprocess
import sys
import signal
import time

children = []

def shutdown(sig, frame):
    for p in children:
        p.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

children.append(
    subprocess.Popen([sys.executable, "app_servicio.py"])
)

children.append(
    subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app_vista.py"])
)

while True:
    time.sleep(1)

