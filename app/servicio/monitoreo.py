import cv2
import time
import traceback
import torch
from ultralytics import YOLO

from servicio.camara import open_rtsp
from servicio.estado_compartido import STATE
from servicio.com_serial import SerialManager
from bd.mongo import insertar_registro_atencion
from bd.modelo import RegistroAtencion


MODEL_PATH = "servicio/modelo/best.pt"

RTSP_READ_TIMEOUT = 2.0     # segundos
RECONNECT_DELAY = 1.0
MAX_FPS_DELAY = 0.03        # ~30 FPS
CUDA_CLEAN_INTERVAL = 100   # frames

ETIQUETAS_MODELO = ["Attentive", "Distracted", "Sleepy", "bullying", "daydreaming", "hand_rising", "human", "phone_use"]


def safe_rtsp_read(cap, timeout=RTSP_READ_TIMEOUT):
    """
    Evita bloqueo infinito de cap.read()
    """
    start = time.time()
    while time.time() - start < timeout:
        ret, frame = cap.read()
        if ret and frame is not None:
            return True, frame
        time.sleep(0.01)
    return False, None


def start_model_loop():
    print("[INIT] Iniciando loop del modelo")

    try:
        model = YOLO(MODEL_PATH)
        class_names = model.names
        print("[INIT] Modelo YOLO cargado")
    except Exception:
        print("[ERROR] Fallo cargando modelo YOLO")
        traceback.print_exc()
        return

    cap = None
    serial_mgr = SerialManager()

    frame_count = 0

    while True:
        try:
            # =======================
            # RTSP
            # =======================
            if cap is None:
                print("[RTSP] Abriendo conexión RTSP...")
                cap = open_rtsp()
                print("[RTSP] Conexión RTSP OK")

            print("[RTSP] Leyendo frame...")
            ret, frame = safe_rtsp_read(cap)

            if not ret:
                print("[RTSP] Timeout leyendo frame. Reconectando...")
                cap.release()
                cap = None
                time.sleep(RECONNECT_DELAY)
                continue

            # =======================
            # MODELO
            # =======================
            print("[MODEL] Ejecutando inferencia...")
            results = model(frame, conf=0.5)
            boxes = results[0].boxes
            print(f"[MODEL] Boxes detectados: {len(boxes)}")

            total = len(boxes)
            atencion_acumulada = 0

            etiquetas_detectadas = []
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                label = class_names[cls].lower()

                porcentaje = conf * 100
                atencion_acumulada += porcentaje

                color = (0, 255, 0) if label in ["atento", "attentive"] else (0, 0, 255)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    frame,
                    f"{label} {porcentaje:.1f}%",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2,
                )

                etiquetas_detectadas.add("")

            estimacion = (atencion_acumulada / total) if total else 0

            # =======================
            # STATE
            # =======================
            print("[STATE] Actualizando estado compartido")
            with STATE.lock:
                STATE.last_frame = frame
                STATE.metrics["estimacion_atencion"] = round(estimacion, 2)
                STATE.metrics["estudiantes_detectados"] = total

            # =======================
            # SERIAL
            # =======================
            print("[SERIAL] Enviando datos a Arduino")
            serial_mgr.send(estimacion) 

            print(
                f"[LOOP] OK | Estudiantes: {total} | "
                f"Estimación: {estimacion:.2f}%"
            )

            # =======================
            # LIMPIEZA GPU
            # =======================
            frame_count += 1
            if torch.cuda.is_available() and frame_count % CUDA_CLEAN_INTERVAL == 0:
                print("[CUDA] Liberando cache GPU")
                torch.cuda.empty_cache()

            # =======================
            # THROTTLING
            # =======================
            time.sleep(MAX_FPS_DELAY)

        except Exception as e:
            print("[ERROR] Excepción capturada en loop principal")
            print(e)
            traceback.print_exc()

            # Reset parcial para recuperación
            try:
                if cap:
                    cap.release()
            except Exception:
                pass

            cap = None
            time.sleep(1)
        
        try:

            registro = {
                "num_estudiantes_detectados": total,
                "porcentaje_estimado_atencion": estimacion,
                "porcentajes_etiquetas": registro.porcentajes_etiquetas,
                "num_deteccion_etiquetas": registro.num_deteccion_etiquetas,
                "fecha_deteccion": registro.fecha_deteccion,
                "hora_detecccion": registro.hora_detecccion,
                "id_horario": registro.id_horario
            }
            insertar_registro_atencion
        except:
            pass