from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
import threading
import cv2

from servicio.estado_compartido import STATE
from servicio.monitoreo import start_model_loop


app = FastAPI()


@app.on_event("startup")
def startup():
    threading.Thread(target=start_model_loop, daemon=True).start()


def frame_generator():
    while True:
        with STATE.lock:
            frame = STATE.last_frame
        if frame is None:
            continue

        _, jpeg = cv2.imencode(".jpg", frame)
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" +
               jpeg.tobytes() + b"\r\n")


@app.get("/stream")
def stream():
    return StreamingResponse(frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/metrics")
def metrics():
    with STATE.lock:
        return JSONResponse(STATE.metrics)