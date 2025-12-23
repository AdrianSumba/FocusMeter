from fastapi import FastAPI
from servicio.modelo_atencion import ultimo_nivel, ultimo_frame
import cv2

app = FastAPI()


@app.get("/estimacion_atencion")
def ultima_estimacion_atencion():
    return {"estimacion_atencion": ultimo_nivel}


@app.get("/frame")
def frame_modelo_atencion():
    if ultimo_frame is None:
        return None

    _, buffer = cv2.imencode(".jpg", ultimo_frame)
    return buffer.tobytes()
