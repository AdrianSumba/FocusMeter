import cv2
from ultralytics import YOLO



ultimo_frame = None
ultimo_nivel = 0.0


def ejecutar_modelo():
    global ultimo_frame, ultimo_nivel
    
    MODEL_PATH = "servicio/modelo_atencion_preentrenado.pt"
    CAMERA_INDEX = 0

    rtsp_url = "rtsp://admin:Novat3ch@192.168.1.5:554/Streaming/Channels/101"
    model = YOLO(MODEL_PATH)
    class_names = model.names

    cap = cv2.VideoCapture(CAMERA_INDEX)
    #cap = cv2.VideoCapture(rtsp_url)
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

        ultimo_nivel = atentos / total if total > 0 else 0
        print(f'\nNivel Atención: {ultimo_nivel}.')


        ultimo_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)