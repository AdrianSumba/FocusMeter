from fastapi import FastAPI
from servicio import modelo_atencion
import cv2
import threading

app = FastAPI()

threading.Thread(target=modelo_atencion.ejecutar_modelo, daemon=True).start()

@app.get("/estimacion_atencion")
def ultima_estimacion_atencion():
    return {"estimacion_atencion": modelo_atencion.ultimo_nivel}

@app.get("/frame")
def frame_modelo_atencion():
    if modelo_atencion.ultimo_frame is None:
        return None
    return modelo_atencion.ultimo_frame


"""from fastapi import FastAPI
from servicio import modelo_atencion
import cv2
import threading

app = FastAPI()

threading.Thread(target=modelo_atencion.ejecutar_modelo, daemon=True).start()

@app.get("/estimacion_atencion")
def ultima_estimacion_atencion():
    return {"estimacion_atencion": modelo_atencion.ultimo_nivel}

@app.get("/frame")
def frame_modelo_atencion():
    if modelo_atencion.ultimo_frame is None:
        return None
    _, buffer = cv2.imencode(".jpg", modelo_atencion.ultimo_frame)
    return buffer.tobytes()
"""