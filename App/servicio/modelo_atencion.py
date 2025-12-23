import cv2
from ultralytics import YOLO
import time

ultimo_frame = None
ultimo_nivel = 0.0


def ejecutar_modelo():
    global ultimo_frame, ultimo_nivel
    
    MODEL_PATH = "servicio/modelo_atencion_preentrenado.pt"
    CAMERA_INDEX = 0

    model = YOLO(MODEL_PATH)
    class_names = model.names

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print('\n No se puede abril la camara, se debe reiniciar el servicio.')
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, conf=0.5)
        boxes = results[0].boxes

        atentos = 0
        total = len(boxes)
        print(f"\nTotal cajas:{total}, atentos: {atentos}")
        time.sleep(1)

        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])

            etiqueta = class_names[cls_id]

            if etiqueta.lower() in ["atento", "attentive"]:
                color = (0, 255, 0)
                atentos += 1
            else:
                color = (0, 0, 255)

            # ===== DIBUJAR CUADRO =====
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame,
                f"{etiqueta} ({conf:.2f})",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

        # ===== NIVEL DE ATENCIÓN (MODELO) =====
        ultimo_nivel = atentos / total if total > 0 else 0
        print(f'\nNivel Atención: {ultimo_nivel}.')


        # ===== MOSTRAR VIDEO =====
        ultimo_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
"""import cv2
import time
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
        print("Total boxes:", total)
        for box in boxes:
            cls_id = int(box.cls[0])
            etiqueta = class_names[cls_id].lower()
            print("Etiqueta detectada:", etiqueta)
            if etiqueta in ["atento", "attentive"]:
                atentos += 1

        ultimo_nivel = atentos / total if total > 0 else 0
        ultimo_frame = frame
        time.sleep(0.03)
        print(f'\n\nNivel atencion: {ultimo_nivel}')
"""