import threading
import time
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from servicio.estado_compartido import STATE
from servicio.monitoreo import start_model_loop


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"] ,
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    threading.Thread(target=start_model_loop, daemon=True).start()


def frame_generator():
    ultimo_enviado = None
    while True:
        with STATE.lock:
            jpeg_bytes = STATE.ultimo_jpeg

        if not jpeg_bytes or jpeg_bytes is ultimo_enviado:
            time.sleep(0.01)
            continue

        ultimo_enviado = jpeg_bytes

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            jpeg_bytes + b"\r\n"
        )

        time.sleep(0.005)


@app.get("/stream")
def stream():
    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )


@app.get("/metrics")
def metrics():
    with STATE.lock:
        data = (STATE.ultimas_metricas or STATE.metrics).copy()
    return JSONResponse(content=data)


@app.websocket("/ws/metrics")
async def websocket_metricas(ws: WebSocket):
    await ws.accept()
    try:
        ultimo_ts = 0.0
        while True:
            with STATE.lock:
                ts = STATE.ts_ultima_actualizacion
                data = (STATE.ultimas_metricas or STATE.metrics).copy()

            if ts != ultimo_ts:
                await ws.send_json(data)
                ultimo_ts = ts

            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        return