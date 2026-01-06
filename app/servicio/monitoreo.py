import cv2
import time
from ultralytics import YOLO

from servicio.camara import open_rtsp
from servicio.estado_compartido import STATE
from servicio.com_serial import SerialManager


MODEL_PATH = "modelo/best.pt"


def start_model_loop():
    model = YOLO(MODEL_PATH)
    class_names = model.names
    cap = open_rtsp()
    serial_mgr = SerialManager()

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        results = model(frame, conf=0.5)
        boxes = results[0].boxes

        total = len(boxes)
        atencion_acumulada = 0

        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            label = class_names[cls].lower()

            porcentaje = conf * 100
            atencion_acumulada += porcentaje

            color = (0,255,0) if label in ["atento", "attentive"] else (0,0,255)

            cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)
            cv2.putText(frame,f"{label} {porcentaje:.1f}%",
                        (x1,y1-10),cv2.FONT_HERSHEY_SIMPLEX,0.6,color,2)

        estimacion = (atencion_acumulada / total) if total else 0

        with STATE.lock:
            STATE.last_frame = frame
            STATE.metrics["estimacion_atencion"] = round(estimacion, 2)
            STATE.metrics["estudiantes_detectados"] = total

        serial_mgr.send(estimacion / 100)
