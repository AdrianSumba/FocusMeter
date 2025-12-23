import cv2
import time
import threading
from ultralytics import YOLO

MODEL_PATH = "servicio/modelo_atencion_preentrenado.pt"
CAMERA_INDEX = 0

model = YOLO(MODEL_PATH)
class_names = model.names

cap = cv2.VideoCapture(CAMERA_INDEX)

ultimo_frame = None
ultimo_nivel = 0.0

def ejecutar_modelo():
    global ultimo_frame, ultimo_nivel

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        results = model(frame, conf=0.5)
        boxes = results[0].boxes

        atentos = 0
        total = len(boxes)

        for box in boxes:
            cls_id = int(box.cls[0])
            etiqueta = class_names[cls_id].lower()
            if etiqueta in ["atento", "attentive"]:
                atentos += 1

        ultimo_nivel = atentos / total if total > 0 else 0
        ultimo_frame = frame

        time.sleep(0.03)

threading.Thread(target=ejecutar_modelo, daemon=True).start()